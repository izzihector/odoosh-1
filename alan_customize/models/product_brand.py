# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['website.multi.mixin']
    _description = 'Product brands'


    name = fields.Char('Brand Name', required=True)
    logo = fields.Binary('Logo File')
    sequence = fields.Integer(string="Sequence")
    product_ids = fields.One2many(
        'product.template',
        'product_brand_id',
        string='Brand Products',
    )
    products_count = fields.Integer(
        string='Number of products',
        compute='_get_products_count',
    )
    visible_slider=fields.Boolean("Visible in Website",default=True)
    active=fields.Boolean("Active",default=True)

    @api.one
    @api.depends('product_ids')
    def _get_products_count(self):
        self.products_count = len(self.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        help='Select a brand for this product'
    )
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        # _logger.info('Launched!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
        self.ensure_one()
        # get the name before the change of context to benefit from prefetch
        display_name = self.name

        quantity = self.env.context.get('quantity', add_qty)
        context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
        product_template = self.with_context(context)

        combination = combination or product_template.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = product_template._get_first_possible_combination(parent_combination)

        if only_template:
            product = product_template.env['product.product']
        elif product_id and not combination:
            product = product_template.env['product.product'].browse(product_id)
        else:
            product = product_template._get_variant_for_combination(combination)

        if product:
            # We need to add the price_extra for the attributes that are not
            # in the variant, typically those of type no_variant, but it is
            # possible that a no_variant attribute is still in a variant if
            # the type of the attribute has been changed after creation.
            no_variant_attributes_price_extra = [
                ptav.price_extra for ptav in combination.filtered(
                    lambda ptav:
                        ptav.price_extra and
                        ptav not in product.product_template_attribute_value_ids
                )
            ]
            if no_variant_attributes_price_extra:
                product = product.with_context(
                    no_variant_attributes_price_extra=no_variant_attributes_price_extra
                )
            list_price = product.price_compute('list_price')[product.id]
            price = product.price if pricelist else list_price
        else:
            product_template = product_template.with_context(current_attributes_price_extra=[v.price_extra or 0.0 for v in combination])
            list_price = product_template.price_compute('list_price')[product_template.id]
            price = product_template.price if pricelist else list_price

        filtered_combination = combination._without_no_variant_attributes()
        filtered_false = False
        for f in filtered_combination.mapped('name'):
            if f == False:
                filtered_false = True
        if filtered_combination:
            if display_name != False and filtered_combination != False and filtered_combination[0] != False and filtered_false == False:
                # _logger.info('___________________-Filtered: ' + str(filtered_combination.mapped('name')[0]) + " _____ " + str(filtered_combination[0]))

                display_name = '%s (%s)' % (display_name, ', '.join(filtered_combination.mapped('name')))
            else:
                return {
                    'product_id': False,
                    'product_template_id': product_template.id,
                    'display_name': "",
                    'price': False,
                    'list_price': False,
                    'has_discounted_price': False,
                }
        if pricelist and pricelist.currency_id != product_template.currency_id:
            list_price = product_template.currency_id._convert(
                list_price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                fields.Date.today()
            )

        price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
        has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount, price) == 1

        return {
            'product_id': product.id,
            'product_template_id': product_template.id,
            'display_name': display_name,
            'price': price,
            'list_price': list_price,
            'has_discounted_price': has_discounted_price,
        }