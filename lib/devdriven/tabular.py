import csv
import json
import tabulate


def formatter(output, fmt, **kwargs):
    if fmt in ("csv"):
        return RecordFormatter(output, fmt, field_sep=",", **kwargs)
    if fmt in ("tsv"):
        return RecordFormatter(output, fmt, field_sep="\t", **kwargs)
    if fmt in ("json"):
        return JSONFormatter(output, fmt, **kwargs)
    if kwargs.get("field_sep"):
        return RecordFormatter(output, fmt, **kwargs)
    return TabularFormatter(output, fmt, **kwargs)


class Formatter:
    def __init__(self, output, fmt, field_sep=None, record_sep=None, **kwargs):
        self.output = output
        self.format = fmt
        self.field_sep = field_sep
        self.record_sep = record_sep
        self.kwargs = kwargs

    def write(self, rows, fields):
        self.write_header(fields)
        self.write_rows(rows, fields)

    def write_header(self, _fields):
        return

    def write_rows(self, rows, fields):
        for row in rows:
            self.write_row(row, fields)

    def write_row(self, _row, _fields):
        # raise NotImplementedError('Formatter.write_row')  # TOO MUCH LINT
        return


class RecordFormatter(Formatter):
    def write(self, rows, fields):
        writer = csv.writer(
            self.output,
            delimiter=self.field_sep,
            lineterminator=(self.record_sep or "\n"),
        )
        writer.writerow(fields)
        for row in rows:
            writer.writerow(extract_record(row, fields))


class JSONFormatter(Formatter):
    def write_row(self, row, fields):
        json.dump(extract_dict(row, fields), self.output)
        self.output.write("\n")


class TabularFormatter(Formatter):
    def write(self, rows, fields):
        rows = [extract_record(row, fields) for row in rows]
        rows.insert(0, fields)
        self.output.write(tabulate.tabulate(rows, tablefmt=self.format))
        self.output.write("\n")


def extract_record(row, fields):
    return [str(row.get(field)) for field in fields]


def extract_dict(row, fields):
    return {field: row.get(field) for field in fields}


def sort_by(rows, fields):
    def row_key(row):
        return [row.get(field, "") for field in fields]

    rows.sort(key=row_key)
    return rows


def uniq_by(seq):
    seen = set()
    result = []
    for elem in seq:
        val = repr(elem)
        if val not in seen:
            seen.add(val)
            result.append(elem)
    return result
