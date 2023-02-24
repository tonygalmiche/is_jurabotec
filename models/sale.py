# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IsSaleOrderColis(models.Model):
    _name='is.sale.order.colis'
    _description = "Colis des commandes"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    name         = fields.Char("Colis", required=True)
    colisage_ids = fields.One2many('is.sale.order.colisage.composant', 'colis_id', 'Colisage')



    def imprimer_fiche_colisage_action(self):
        for obj in self:
            report=self.env.ref('is_jurabotec.is_sale_order_colis_reports')
            return report.report_action([obj.id])



class IsSaleOrderColisageComposant(models.Model):
    _name='is.sale.order.colisage.composant'
    _description = "Colisage des composants"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    colis_id     = fields.Many2one('is.sale.order.colis', 'Colis', group_expand='_group_expand_colis_id')
    #product_id   = fields.Many2one('product.product', 'Article')
    product_id   = fields.Many2one("product.product", string="Catégorie de clientArticle", related="sale_line_id.product_id", readonly=True)
    composant_id = fields.Many2one('product.product', 'Composant')
    qty          = fields.Float(string='Quantité', digits='Product Unit of Measure')
    sale_line_id = fields.Many2one('sale.order.line', 'Ligne de commande', required=True)
    colis_ids    = fields.Many2many('is.sale.order.colis', 'is_sale_order_line_colis_ids', 'line_id', 'colis_id', store=False, readonly=True, compute='_compute_colis_ids', string="Colis autorisés")


    @api.depends('colis_id')
    def _compute_colis_ids(self):
        for obj in self:
            ids=[]
            for colis in obj.order_id.is_colis_ids:
                ids.append(colis.id)
            obj.colis_ids= [(6, 0, ids)]


    @api.model
    def _group_expand_colis_id(self, stages, domain, order):
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
        colis = stages.order_id.is_colis_ids
        return colis


    def dupliquer_colis_action(self):
        for obj in self:
            print(obj)
            res=obj.copy()
            res.qty=0



class sale_order(models.Model):
    _inherit = "sale.order"

    is_delai             = fields.Date('Délai')
    is_colis_ids         = fields.One2many('is.sale.order.colis'             , 'order_id', 'Colis')
    is_colisage_ids      = fields.One2many('is.sale.order.colisage.composant', 'order_id', 'Colisage')
    is_num_cde_client    = fields.Char('N° commande client')
    is_detail_composants = fields.Boolean('Imprimer le détail des composants', default=False)


    def colisage_action(self):
        for obj in self:
            if len(obj.is_colisage_ids)==0:
                for line in obj.order_line:
                    filtre=[
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                        ('type'           , '=', 'commande'),
                    ]
                    boms = self.env['mrp.bom'].search(filtre,limit=1)
                    if len(boms)>0:
                        for bom_line in boms[0].bom_line_ids:
                            vals={
                                "colis_id": obj.is_colis_ids[0].id,
                                "order_id": obj.id,
                                "composant_id": bom_line.product_id.id,
                                "qty": line.product_uom_qty*bom_line.product_qty,
                                "sale_line_id": line.id,
                            }
                            res = self.env['is.sale.order.colisage.composant'].create(vals)

            return {
                "name": "Colisage des composants %s"%(obj.name),
                "view_mode": "kanban,tree,form",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }


    def liste_colis_action(self):
        for obj in self:
           return {
                "name": "Colis %s"%(obj.name),
                "view_mode": "tree,form",
                "res_model": "is.sale.order.colis",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_composants     = fields.Html(string='Composants', compute='_compute_is_composants')
    is_composants_ids = fields.One2many('is.sale.order.colisage.composant', 'sale_line_id', 'Lignes des composants')


    def _compute_is_composants(self):
        for obj in self:
            t=[]
            for line in obj.is_composants_ids:
                t.append("<div>- %s x %s</div>"%(line.qty, line.composant_id.name))
            html = "\n".join(t)
            obj.is_composants = html

