from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "sale", "migrations/1.3/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "sale",
        [
            "email_template_edi_sale",
            "mail_template_sale_confirmation",
        ],
    )