import re
from rest_framework.parsers import MultiPartParser, DataAndFiles

def safe_list_get(l, idx, default=None):
    try:
        return l[idx]
    except IndexError:
        return default

class MultiPartJSONParser(MultiPartParser):

    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type, parser_context)
        data = {}
        files = {}

        for key, value in result.data.items():
            self._deep_set(data, key, value)

        for key, value in result.files.items():
            self._deep_set(files, key, value)

        parsed_data = self._merge_data_files(data,files)
        return parsed_data


    def _deep_set(self, data, key, value):
        keys = self._parse_keys(key)
        d = data
        for i, part in enumerate(keys):
            if part.isdigit():
                part = int(part)
                if i == len(keys) - 1:
                    if isinstance(d, list):
                        while len(d) <= part:
                            d.append({})
                        d[part] = value
                    else:
                        d[part] = value
                else:
                    if isinstance(d, list):
                        while len(d) <= part:
                            d.append({})
                        if not isinstance(d[part], dict):
                            d[part] = {}
                        d = d[part]
                    else:
                        if part not in d or not isinstance(d[part], dict):
                            d[part] = {}
                        d = d[part]
            else:
                if i == len(keys) - 1:
                    d[part] = value
                else:
                    if part not in d or not isinstance(d[part], dict):
                        d[part] = {}
                    d = d[part]

    @staticmethod
    def _parse_keys(key):
        return re.split(r'\[|\]\[|\]', key.strip('[]'))

    @staticmethod
    def merge_data_files(data, files):
        merged_data = {}

        for key, value in files.items():
            keys = key.split('[')
            main_key = keys[0]
            index = None
            if len(keys) > 1:
                index = int(keys[1].strip(']'))

            if main_key in merged_data:
                if isinstance(merged_data[main_key], list):
                    if index is not None:
                        while len(merged_data[main_key]) <= index:
                            merged_data[main_key].append({})
                        merged_data[main_key][index].update({keys[-1].strip(']'): value})
                    else:
                        merged_data[main_key].append({keys[-1].strip(']'): value})
                else:
                    merged_data[main_key] = [{keys[-1].strip(']'): value}]
            else:
                if index is not None:
                    merged_data[main_key] = [{keys[-1].strip(']'): value}]
                else:
                    merged_data[main_key] = value

        for key, value in data.items():
            if key in merged_data:
                if isinstance(merged_data[key], list):
                    for item in merged_data[key]:
                        if isinstance(item, dict) and main_key in item:
                            item.update(value)
                elif isinstance(merged_data[key], dict):
                    if main_key in merged_data[key]:
                        merged_data[key].update(value)
                else:
                    merged_data[key] = [merged_data[key], value]
            else:
                merged_data[key] = value

        return merged_data

    def _merge_data_files(self,data, files):
        merged_data = {}

        for key, value in data.items():
            if isinstance(value, dict):
                if key in files:
                    merged_items = []
                    for doc_key, doc_value in value.items():
                        merged_item = {**files[key].get(doc_key, {}), **doc_value}
                        merged_items.append(merged_item)
                    merged_data[key] = merged_items
                else:
                    merged_items = []
                    for data_key, data_value in value.items():
                        merged_item = {**files.get(data_key, {}), **data_value}
                        merged_items.append(merged_item)
                    merged_data[key] = merged_items
            else:
                if key in files:
                    merged_data[key] = files[key]
                else:
                    merged_data[key] = value

        for file_key, file_value in files.items():
            if file_key not in merged_data:
                merged_data[file_key] = file_value

        return merged_data
