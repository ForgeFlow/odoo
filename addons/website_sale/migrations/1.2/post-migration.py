from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "website_sale", "migrations/1.2/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "sale",
        [
            "mail_template_sale_cart_recovery",
        ],
    )