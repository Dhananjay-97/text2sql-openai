def get_db_metadata(cursor):
    query = """
    WITH metadata AS (
        SELECT
            t.table_name AS table_name,
            t.column_name AS column_name,
            t.data_type AS data_type,
            NVL(c.comments, 'N/A') AS column_comments
        FROM user_tab_columns t
        LEFT JOIN user_col_comments c
            ON t.table_name = c.table_name
            AND t.column_name = c.column_name
        WHERE t.table_name IN (SELECT table_name FROM user_tables) -- Exclude views
    ),
    table_properties AS (
        SELECT
            ut.table_name AS table_name,
            NVL(tc.comments, 'N/A') AS table_comments
        FROM user_tables ut
        LEFT JOIN user_tab_comments tc
            ON ut.table_name = tc.table_name
    ),
    foreign_keys AS (
        SELECT
            uc.table_name AS table_name,
            ucc.column_name AS column_name,
            uc.constraint_name AS foreign_key,
            rc.table_name AS referred_table,
            rcc.column_name AS referred_column
        FROM user_constraints uc
        JOIN user_cons_columns ucc
            ON uc.constraint_name = ucc.constraint_name
        JOIN user_constraints rc
            ON uc.r_constraint_name = rc.constraint_name
        JOIN user_cons_columns rcc
            ON rc.constraint_name = rcc.constraint_name
        WHERE uc.constraint_type = 'R' -- 'R' indicates foreign key constraints
    ),
    combined_metadata AS (
        SELECT
            m.table_name,
            m.column_name,
            m.data_type,
            m.column_comments,
            tp.table_comments,
            fk.foreign_key,
            fk.referred_table,
            fk.referred_column
        FROM metadata m
        LEFT JOIN table_properties tp
            ON m.table_name = tp.table_name
        LEFT JOIN foreign_keys fk
            ON m.table_name = fk.table_name
            AND m.column_name = fk.column_name
    )
    SELECT JSON_OBJECTAGG(
            table_name VALUE metadata_json RETURNING CLOB
        ) AS schema_metadata_json
    FROM (
        SELECT
            table_name,
            JSON_OBJECT(
                'table_comments' VALUE MAX(table_comments),
                'columns' VALUE JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'column_name' VALUE column_name,
                        'data_type' VALUE data_type,
                        'column_comments' VALUE column_comments,
                        'foreign_key' VALUE foreign_key,
                        'referred_table' VALUE referred_table,
                        'referred_column' VALUE referred_column
                    ) RETURNING CLOB
                ) RETURNING CLOB
            ) AS metadata_json
        FROM combined_metadata
        GROUP BY table_name
    )
    """

    cursor.execute(query)
    return cursor.fetchone()
