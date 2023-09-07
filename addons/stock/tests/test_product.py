# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Author: Leonardo Pistone
# Copyright 2015 Camptocamp SA

from odoo.addons.stock.tests.common2 import TestStockCommon


class TestVirtualAvailable(TestStockCommon):

    def setUp(self):
        super(TestVirtualAvailable, self).setUp()

        # Make `product3` a storable product for this test. Indeed, creating quants
        # and playing with owners is not possible for consumables.
        self.product_3.type = 'product'

        self.env['stock.quant'].create({
            'product_id': self.product_3.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'quantity': 30.0})

        self.env['stock.quant'].create({
            'product_id': self.product_3.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'quantity': 10.0,
            'owner_id': self.user_stock_user.partner_id.id})

        self.picking_out = self.env['stock.picking'].create({
            'picking_type_id': self.ref('stock.picking_type_out'),
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id})
        self.env['stock.move'].create({
            'name': 'a move',
            'product_id': self.product_3.id,
            'product_uom_qty': 3.0,
            'product_uom': self.product_3.uom_id.id,
            'picking_id': self.picking_out.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id})

        self.picking_out_2 = self.env['stock.picking'].create({
            'picking_type_id': self.ref('stock.picking_type_out'),
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id})
        self.env['stock.move'].create({
            'restrict_partner_id': self.user_stock_user.partner_id.id,
            'name': 'another move',
            'product_id': self.product_3.id,
            'product_uom_qty': 5.0,
            'product_uom': self.product_3.uom_id.id,
            'picking_id': self.picking_out_2.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id})

    def test_without_owner(self):
        self.assertAlmostEqual(40.0, self.product_3.virtual_available)
        self.picking_out.action_assign()
        self.picking_out_2.action_assign()
        self.assertAlmostEqual(32.0, self.product_3.virtual_available)

    def test_with_owner(self):
        prod_context = self.product_3.with_context(owner_id=self.user_stock_user.partner_id.id)
        self.assertAlmostEqual(10.0, prod_context.virtual_available)
        self.picking_out.action_assign()
        self.picking_out_2.action_assign()
        self.assertAlmostEqual(5.0, prod_context.virtual_available)

    def test_product_qty_field_and_context(self):
        main_warehouse = self.warehouse_1
        other_warehouse = self.env['stock.warehouse'].search([('id', '!=', main_warehouse.id)], limit=1)
        warehouses = main_warehouse | other_warehouse
        main_loc = main_warehouse.lot_stock_id
        other_loc = other_warehouse.lot_stock_id
        self.assertTrue(other_warehouse, 'The test needs another warehouse')

        (main_loc | other_loc).name = 'Stock'
        sub_loc01, sub_loc02, sub_loc03 = self.env['stock.location'].create([{
            'name': 'Sub0%s' % (i + 1),
            'location_id': main_loc.id,
        } for i in range(3)])

        self.env['stock.quant'].search([('product_id', '=', self.product_3.id)]).unlink()
        self.env['stock.quant']._update_available_quantity(self.product_3, other_loc, 1000)
        self.env['stock.quant']._update_available_quantity(self.product_3, main_loc, 100)
        self.env['stock.quant']._update_available_quantity(self.product_3, sub_loc01, 10)
        self.env['stock.quant']._update_available_quantity(self.product_3, sub_loc02, 1)

        for wh, loc, expected in [
            (False, False, 1111.0),
            (False, other_loc.id, 1000.0),
            (False, main_loc.id, 111.0),
            (False, sub_loc01.id, 10.0),
            (False, sub_loc01.name, 10.0),
            (False, 'sub', 11.0),
            (False, main_loc.name, 1111.0),
            (False, (sub_loc01 | sub_loc02 | sub_loc03).ids, 11.0),
            (main_warehouse.id, main_loc.name, 111.0),
            (main_warehouse.id, main_loc.id, 111.0),
            (main_warehouse.id, (main_loc | other_loc).ids, 111.0),
            (main_warehouse.id, sub_loc01.id, 10.0),
            (main_warehouse.id, (sub_loc01 | sub_loc02).ids, 11.0),
            (other_warehouse.id, main_loc.name, 1000.0),
            (other_warehouse.id, main_loc.id, 0.0),
            (main_warehouse.name, False, 111.0),
            (main_warehouse.id, False, 111.0),
            (warehouses.ids, False, 1111.0),
            (warehouses.ids, (other_loc | sub_loc02).ids, 1001),
        ]:
            product_qty = self.product_3.with_context(warehouse=wh, location=loc).qty_available
            self.assertEqual(product_qty, expected)
