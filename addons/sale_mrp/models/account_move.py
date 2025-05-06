# -*- coding: utf-8 -*-

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _stock_account_get_anglo_saxon_price_unit(self):
        price_unit = super(AccountMoveLine, self)._stock_account_get_anglo_saxon_price_unit()

        so_line = self.sale_line_ids and self.sale_line_ids[-1] or False
        if so_line:
            # BUG in core: if you have a variant bom in a different company than the
            # SO company it will be taken and then in the filtered it will be gone
            # In order to reproduce the bug you have to have
            # a variant bom in another company than SO company
            # a product template bom in the SO company
            # in your environment have the two companies activated (if you only have
            # one company activated the bug will not show because the variant bom
            # is not found).
            # The fix is giving preference to the bom of the sale line
            boms = so_line.move_ids.filtered(lambda m: m.state != 'cancel').mapped('bom_line_id.bom_id').filtered(lambda b: b.type == 'phantom')
            bom = (boms or self.env['mrp.bom']._bom_find(product=so_line.product_id, company_id=so_line.company_id.id, bom_type='phantom'))[:1]
            if bom:
                is_line_reversing = bool(self.move_id.reversed_entry_id)
                qty_to_invoice = self.product_uom_id._compute_quantity(self.quantity, self.product_id.uom_id)
                posted_invoice_lines = so_line.invoice_lines.filtered(lambda l: l.move_id.state == 'posted' and bool(l.move_id.reversed_entry_id) == is_line_reversing)
                qty_invoiced = sum([x.product_uom_id._compute_quantity(x.quantity, x.product_id.uom_id) for x in posted_invoice_lines])
                moves = so_line.move_ids
                average_price_unit = 0
                components_qty = so_line._get_bom_component_qty(bom)
                storable_components = self.env['product.product'].search([('id', 'in', list(components_qty.keys())), ('type', '=', 'product')])
                for product in storable_components:
                    factor = components_qty[product.id]['qty']
                    prod_moves = moves.filtered(lambda m: m.product_id == product)
                    prod_qty_invoiced = factor * qty_invoiced
                    prod_qty_to_invoice = factor * qty_to_invoice
                    average_price_unit += factor * product.with_context(force_company=self.company_id.id, is_returned=is_line_reversing)._compute_average_price(prod_qty_invoiced, prod_qty_to_invoice, prod_moves)
                price_unit = average_price_unit / bom.product_qty or price_unit
                price_unit = self.product_id.uom_id._compute_price(price_unit, self.product_uom_id)
        return price_unit
