# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    tax_certificate = fields.Binary("Tax Certificate")
    filename = fields.Char("Filename")
    comments = fields.Text("Comments")
    account_type = fields.Selection([('hospitality', 'Hospitality - Commercial Design'), ('stocking_dealer', 'Stocking Dealer - $2,500 Opening Order - ($2,500 Yearly) - Save 30% over wholesale'), ('wholesale_account', 'Wholesale Account - No Minium Order - (No Commitment)')], string='Account Required')
