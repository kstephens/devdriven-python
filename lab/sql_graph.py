from dataclasses import dataclass, field
from typing import Any, Dict, List
from icecream import ic


"""
ruff format lab/sql_graph.py; python3 lab/sql_graph.py | tee >(nl > /dev/stderr) | intg psql production-read-replica

"""


def field_list():
    return field(default_factory=list)


def field_dict():
    return field(default_factory=dict)


@dataclass
class Column:
    name: str
    is_pk: bool = field(default=False)
    expr: str | None = field(default=None)
    output_alias: str = field(default="")
    table: Any = None

    @property
    def full_name(self) -> str:
        return f"{self.table.full_name}.{self.name}"

    @property
    def alias_name(self) -> str:
        return f"{self.table.alias_name}__{self.name}"

    def __repr__(self):
        return f"Column({self.full_name!r}, {self.is_pk})"


@dataclass
class Table:
    name: str
    id_column: Column | None = field(default=None)
    columns: List[Column] = field_list()
    column_by_name: Dict[str, Column] = field_dict()
    schema: Any = field(default=None)

    @property
    def full_name(self) -> str:
        return f"{self.schema.full_name}.{self.name}"

    @property
    def alias_name(self) -> str:
        return f"{self.schema.alias_name}__{self.name}"

    def column(self, name: str) -> Column:
        return self.column_by_name.get(name) or self.add_column(Column(name=name))

    def add_column(self, column: Column):
        assert column.name not in self.column_by_name
        self.column_by_name[column.name] = column
        self.columns.append(column)
        column.table = self
        return column


@dataclass
class Schema:
    name: str
    tables: List[Table] = field_list()
    table_by_name: Dict[str, Table] = field_dict()

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def alias_name(self):
        return self.name

    def table(self, name: str) -> Table:
        if table := self.table_by_name.get(name):
            return table
        table = self.add_table(Table(name))
        table.id_column = table.add_column(Column(name="id", is_pk=True))
        return table

    def add_table(self, table: Table):
        assert table.name not in self.table_by_name
        self.table_by_name[table.name] = table
        self.tables.append(table)
        table.schema = self
        return table


@dataclass
class Join:
    a: Column
    b: Column
    kind: str = field(default="JOIN")

    @property
    def expr(self) -> str:
        return f"{self.kind} {self.a.table.full_name} ON {self.a.name} = {self.b.name}"


@dataclass
class Relations:
    schemas: List[Schema] = field_list()
    schema_by_name: Dict[str, Schema] = field_dict()
    joins: List[Join] = field_list()

    def schema(self, name: str) -> Schema:
        return self.schema_by_name.get(name) or self.add_schema(Schema(name))

    def table(self, path: str) -> Table:
        schema_name, table_name = path.split(".")
        return self.schema(schema_name).table(table_name)

    def column(self, path: str) -> Column:
        schema_name, table_name, column_name = path.split(".")
        return self.schema(schema_name).table(table_name).column(column_name)

    @property
    def columns(self):
        cols = []
        for schema in self.schemas:
            for table in schema.tables:
                cols.extend(table.columns)
        return cols

    def add_schema(self, schema: Schema):
        assert schema.name not in self.schema_by_name
        self.schemas.append(schema)
        self.schema_by_name[schema.name] = schema
        return schema

    def join(self, kind: str, a: Column, b: Column):
        join = Join(a, b, kind)
        self.joins.append(join)
        ic(join)
        return join

    def query(self) -> str:
        sql = ""
        lines = []
        cols: List[str] = []
        cols_seen: set = set()
        joins: List[str] = []
        table_seen: set = set()

        def add_line(s):
            lines.append(s)

        def add_column(c):
            ic(c)
            name = f'{c.table.alias_name}.{c.name} AS "{c.output_alias}"'
            if c.full_name in cols_seen:
                return
            cols_seen.add(c.full_name)
            ic(name)
            if cols:
                name = f"  , {name}"
            else:
                name = f"    {name}"
            cols.append(name)

        def add_join(j):
            a_alias = f'{j.a.table.full_name} AS "{j.a.table.alias_name}"'
            b_alias = f'{j.b.table.full_name} AS "{j.b.table.alias_name}"'
            if not joins:
                s = f"FROM {b_alias}"
                if b_alias not in table_seen:
                    table_seen.add(b_alias)
                    joins.append(s)
            s = f"{j.kind} {a_alias} ON {j.a.table.alias_name}.{j.a.name} = {j.b.table.alias_name}.{j.b.name}"
            if a_alias not in table_seen:
                table_seen.add(a_alias)
                joins.append(s)

        ic(self.columns)
        for c in self.columns:
            if c.output_alias:
                add_column(c)
        for c in self.joins:
            add_join(c)
        sql += f"""
SELECT DISTINCT * FROM (
SELECT
{"\n".join(cols)}
{"\n".join(joins)}
)
WHERE 1=1
AND customer_id = 11500003
LIMIT 10
"""
        return sql


def build_relations() -> Relations:
    relations = Relations()

    join_defs = [
        [
            "LEFT JOIN",
            "accounts.customer_accounts.customer_id",
            "customers.customers.id",
        ],
        [
            "LEFT JOIN",
            "customers.customer_infos.customer_id",
            "customers.customers.id",
        ],
        [
            "LEFT JOIN",
            "customers.residences.customer_id",
            "customers.customers.id",
        ],
        [
            "JOIN",
            "customers.addresses.id",
            "customers.residences.address_id",
        ],
        [
            "JOIN",
            "customers.postal_codes.id",
            "customers.addresses.postal_code_id",
        ],
        [
            "JOIN",
            "enums.state_provinces.id",
            "customers.addresses.state_province_id",
        ],
        [
            "LEFT JOIN",
            "customers.time_spans.id",
            "customers.residences.time_at_address_id",
        ],
        [
            "LEFT JOIN",
            "customers.residence_types.id",
            "customers.residences.residence_type_id",
        ],
        [
            "LEFT JOIN",
            "customers.customer_email_addresses.customer_id",
            "customers.customers.id",
        ],
        [
            "JOIN",
            "customers.email_addresses.id",
            "customers.customer_email_addresses.email_address_id",
        ],
        [
            "JOIN",
            "payment_gateway.customer_bank_accounts.customer_id",
            "customers.customers.id",
        ],
        [
            "JOIN",
            "payment_gateway.customer_bank_account_infos.customer_bank_account_id",
            "payment_gateway.customer_bank_accounts.id",
        ],
        [
            "LEFT JOIN",
            "customers.employments.customer_id",
            "customers.customers.id",
        ],
        [
            "JOIN",
            "customers.employment_infos.id",
            "customers.employments.id",
        ],
        [
            "JOIN",
            "customers.employer_names.id",
            "customers.employment_infos.employer_name_id",
        ],
        [
            "JOIN",
            "customers.person_names.id",
            "customers.customer_infos.person_name_id",
        ],
    ]
    col_defs = [
        "customers.customers.id",
        "customers.email_addresses.id",
        "customers.email_addresses.full_address",
        "payment_gateway.customer_bank_account_infos.id",
    ]
    output_cols = {
        "customers.customers.id": "customer_id",
        "accounts.customer_accounts.id": "customer_account_id",
        "customers.email_addresses.full_address": "email_address",
        "customers.person_names.first_name": True,
        "customers.person_names.last_name": True,
        "customers.addresses.line1": "address_line1",
        "customers.addresses.line2": "address_line2",
        "customers.postal_codes.postcode": "address_postcode",
        "customers.time_spans.name": "time_at_address",
        "customers.residence_types.name": "residence_type",
        "payment_gateway.customer_bank_account_infos.routing_number": "routing_number",
        "payment_gateway.customer_bank_account_infos.account_number": "account_number",
        "customers.employer_names.name": "employer_name",
    }

    for col_def in col_defs:
        relations.column(col_def)

    for col_name, output_name in output_cols.items():
        column = relations.column(col_name)
        column.output_alias = str(column.name if output_name is True else output_name)

    for join_def in join_defs:
        kind, a, b, *opts = join_def
        relations.join(kind, relations.column(a), relations.column(b))

    ic(relations.columns)
    ic(relations.joins)

    print(relations.query())
    return relations


def main():
    build_relations()


main()
