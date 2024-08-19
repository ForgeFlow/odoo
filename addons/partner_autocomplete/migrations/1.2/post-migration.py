from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE res_partner
            ADD COLUMN IF NOT EXISTS old_additional_info VARCHAR;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE res_partner
            SET old_additional_info = additional_info;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE res_partner
            SET additional_info = ''
            WHERE NOT is_valid_json(additional_info);
        """,
        )
