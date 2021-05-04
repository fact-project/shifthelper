from secrets import token_hex
from sqlalchemy import text

#: query to get column names for a specific table (MYSQL)
query_column_names = text('''
SELECT `COLUMN_NAME`
FROM `INFORMATION_SCHEMA`.`COLUMNS`
WHERE
    `TABLE_SCHEMA`= :database
    AND `TABLE_NAME`= :table
;
''')

def get_column_names(con, table):
    '''Get all columns of a mysql table'''
    result = con.execute(query_column_names, dict(database=con.engine.url.database, table=table))
    return [r._mapping["COLUMN_NAME"] for r in result.all()]


def build_insert_query(con, table, columns=None):
    '''Create an insert query for all columns of a database'''
    if columns is None:
        columns = get_column_names(con, table)

    params = ", ".join(f":{c}" for c in columns)

    lines = [
        f'INSERT INTO {table}',
        '  (' + ', '.join(columns) + ')',
        'VALUES',
        '  (' + params + ')'
        ';'
    ]
    return text('\n'.join(lines))


def get_create_table(con, table, new_name=None):
    '''
    Get the mysql query to recreate the table, optionally altering the name.
    '''
    result  = con.execute(text(f"SHOW CREATE TABLE {table}"))
    schema = result.one()[1]
    if new_name is not None:
        schema = schema.replace(f"CREATE TABLE `{table}`", f"CREATE TABLE `{new_name}`")
    return text(schema)


def copy_table(
    engine_in,
    engine_out,
    table,
    select_query=None,
    create_query=None,
    insert_query=None,
    output_table=None
):

    with engine_out.begin() as con_out, engine_in.begin() as con_in:

        # to make the write atomic, we write to a temp table and then rename
        tmp_table = "tmp" + token_hex(8)

        # create the table with the same schema and name if none of the options
        # are given
        if output_table is None:
            output_table = table

        if create_query is None:
            create_query = get_create_table(con_in, table, new_name=tmp_table)

        # recreate tmp table
        con_out.execute(create_query)

        # get data from the input table
        if select_query is None:
            select_query = text(f"SELECT * FROM `{table}`")

        rows = con_in.execute(select_query).all()

        # no data, nothing left to do
        if len(rows) > 0:
            # insert data into new table
            if insert_query is None:
                insert_query = build_insert_query(con_out, tmp_table)
            n_new = con_out.execute(insert_query, [r._mapping for r in rows]).rowcount
        else:
            n_new = 0


        if con_out.dialect.has_table(con_out, output_table):
            # if the table already exists, we need to switch old and new,
            # then drop the old table
            drop_table = tmp_table + "drop"
            rename_query = text(f"RENAME TABLE `{output_table}`  to `{drop_table}`, `{tmp_table}` to `{output_table}`;")
            drop_query = text(f"DROP TABLE `{drop_table}`")

        else:
            # if not, we can just rename the tmp table to the target name
            rename_query = text(f"RENAME TABLE `{tmp_table}` to `{output_table}`")
            drop_query = None

        con_out.execute(rename_query)
        if drop_query is not None:
            con_out.execute(drop_query)

        return n_new
