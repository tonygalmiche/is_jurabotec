# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IsSaleOrderColis(models.Model):
    _name='is.sale.order.colis'
    _description = "Colis des commandes"

    order_id = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    name   = fields.Char("Colis", required=True)


class IsSaleOrderColisageComposant(models.Model):
    _name='is.sale.order.colisage.composant'
    _description = "Colisage des composants"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    colis_id     = fields.Many2one('is.sale.order.colis', 'Colis', group_expand='_group_expand_colis_id')
    product_id   = fields.Many2one('product.product', 'Article')
    composant_id = fields.Many2one('product.product', 'Composant')
    sale_line_id = fields.Many2one('sale.order.line', 'Ligne de commande')


    @api.model
    def _group_expand_colis_id(self, stages, domain, order):
        print("## _group_expand_colis_id",self, stages, domain, order)
        print(self.order_id.is_colis_ids)
        # # retrieve team_id from the context and write the domain
        # # - ('id', 'in', stages.ids): add columns that should be present
        # # - OR ('fold', '=', False): add default columns that are not folded
        # # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        # team_id = self._context.get('default_team_id')
        # if team_id:
        #     search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        # else:
        #     search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # # perform search
        # stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)

        colis = self.env['is.sale.order.colis'].search([])
        print("colis 1",colis)

        colis = stages.order_id.is_colis_ids
        print("colis 2",colis)


        return colis

        #return stages.browse(self.)

## _group_expand_colis_id is.sale.order.colisage.composant() is.sale.order.colis(1,) [['order_id', '=', 1]] id



class sale_order(models.Model):
    _inherit = "sale.order"

    is_colis_ids    = fields.One2many('is.sale.order.colis', 'order_id', 'Colis')
    is_colisage_ids = fields.One2many('is.sale.order.colisage.composant', 'order_id', 'Colisage')

    def colisage_action(self):
        for obj in self:
            print(obj)
            if len(obj.is_colisage_ids)==0:
                for line in obj.order_line:
                    filtre=[('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)]
                    print(filtre)
                    boms = self.env['mrp.bom'].search(filtre)
                    print(line.product_id,boms)
                    if len(boms)>0:
                        for bom_line in boms[0].bom_line_ids:
                            print("-",bom_line.product_id)
                            vals={
                                "colis_id": obj.is_colis_ids[0].id,
                                "order_id": obj.id,
                                "product_id": line.product_id.id,
                                "composant_id": bom_line.product_id.id,
                                "sale_line_id": line.id,
                            }
                            res = self.env['is.sale.order.colisage.composant'].create(vals)

            return {
                "name": "Colisage des composants %s"%(obj.name),
                "view_mode": "kanban,tree",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }
