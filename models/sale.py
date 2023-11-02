# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IsSaleOrderColis(models.Model):
    _name='is.sale.order.colis'
    _description = "Colis des commandes"
    _order='sequence'

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    sequence     = fields.Integer("Ordre")
    name         = fields.Char("Colis", required=True)
    colisage_ids = fields.One2many('is.sale.order.colisage.composant', 'colis_id', 'Colisage')


    def imprimer_fiche_colisage_action(self):
        for obj in self:
            report=self.env.ref('is_jurabotec.is_sale_order_colis_reports')
            return report.report_action([obj.id])


    def repartir_colis_action(self):
        for obj in self:
            print(obj,obj.colisage_ids)

    def lignes_colis_action(self):
        for obj in self:
            print(obj,obj.colisage_ids)

            return {
                "name": obj.name,
                "view_mode": "tree,form",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("colis_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_colis_action(self):
        for obj in self:
            res= {
                'name': obj.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res






class IsSaleOrderColisageComposant(models.Model):
    _name='is.sale.order.colisage.composant'
    _description = "Colisage des composants"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    colis_id     = fields.Many2one('is.sale.order.colis', 'Colis', group_expand='_group_expand_colis_id', required=True)
    #product_id   = fields.Many2one('product.product', 'Article')
    product_id   = fields.Many2one("product.product", string="Article", related="sale_line_id.product_id", readonly=True)
    composant_id = fields.Many2one('product.product', 'Composant')
    qty          = fields.Float(string='Quantité', digits='Product Unit of Measure')
    qty_bom      = fields.Float(string='Qt nomenclature', digits='Product Unit of Measure')
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
            res=obj.copy()
            res.qty=0


    def voir_colis_action(self):
        for obj in self:
            print(obj)

            res= {
                'name': obj.colis_id.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.colis_id.id,
                'type': 'ir.actions.act_window',
            }
            return res




           

class sale_order(models.Model):
    _inherit = "sale.order"

    is_delai             = fields.Date('Délai')
    is_colis_ids         = fields.One2many('is.sale.order.colis'             , 'order_id', 'Colis')
    is_colisage_ids      = fields.One2many('is.sale.order.colisage.composant', 'order_id', 'Colisage')
    is_num_cde_client    = fields.Char('N° commande client')
    is_detail_composants = fields.Boolean('Imprimer le détail des composants', default=False)
    is_devis_id          = fields.Many2one('sale.order', "Devis d'origine", copy=False, readonly=True)


    def convertir_en_commande_action(self):
        for obj in self:
            copy = obj.copy()
            copy.is_devis_id = obj.id
            res= {
                'name': copy.name,
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': copy.id,
                'type': 'ir.actions.act_window',
            }
            return res


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
                    else:
                        vals={
                            "colis_id": obj.is_colis_ids[0].id,
                            "order_id": obj.id,
                            "composant_id": line.product_id.id,
                            "qty": line.product_uom_qty,
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
    is_prix_tarif  = fields.Float(string="Prix tarif", digits='Product Unit of Measure', help="Tarif de la liste de prix")
    is_unite_tarif = fields.Selection([
        ('m'    , 'm'),
        ('m2'   , 'm2'),
        ('m3'   , 'm3'),
        ('unite', 'Unité'),
    ], "Unité", help="Unité de la liste de prix")
    is_longueur        = fields.Float(string="Longueur",        digits='Product Unit of Measure', related="product_id.is_longueur", readonly=True)
    is_longueur_totale = fields.Float(string="Longueur totale", digits='Product Unit of Measure')
    is_surface         = fields.Float(string="Surface",         digits='Product Unit of Measure', related="product_id.is_surface", readonly=True)
    is_surface_totale  = fields.Float(string="Surface totale",  digits='Product Unit of Measure')
    is_volume          = fields.Float(string="Volume",          digits='Volume', related="product_id.is_volume", readonly=True)
    is_volume_total    = fields.Float(string="Volume total",    digits='Volume')
    is_detail_quantite = fields.Text(string='Détail quantité', compute='_compute_is_detail_quantite')


    @api.depends('product_id', 'product_uom_qty', 'is_longueur_totale', 'is_surface_totale', 'is_volume_total')
    def _compute_is_detail_quantite(self):
        for obj in self:
            x = False
            if obj.product_uom_qty and obj.is_longueur  and obj.is_longueur_totale and obj.is_surface_totale:
                x = "En longueur de %.1fm soit %.1fml ou %.1fm2"%(obj.is_longueur, obj.is_longueur_totale, obj.is_surface_totale)
            obj.is_detail_quantite = x


    @api.depends('product_id', 'product_uom', 'product_uom_qty','is_prix_tarif','is_unite_tarif','product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            price = 0
            for l in line.product_id.product_template_variant_value_ids:
                if l.attribute_line_id.attribute_id.name=="Longueur":
                    variante = l.product_attribute_value_id.name
                    if variante in ['ml','m2','m','u']:
                        price = line.is_prix_tarif
            if price==0:
                if line.is_unite_tarif=="m":
                    price = line.is_prix_tarif*line.is_longueur
                if line.is_unite_tarif=="m2":
                    price = line.is_prix_tarif*line.is_surface
                if line.is_unite_tarif=="m3":
                    price = line.is_prix_tarif*line.is_volume
                if line.is_unite_tarif=="unite":
                    price = line.is_prix_tarif
            line.price_unit = price


    @api.onchange('product_id','product_template_id', 'product_uom_qty')
    def _onchange_product_id(self):
        price = 0
        unite = False
        pricelist = self.order_id.pricelist_id
        if pricelist:
            for line in pricelist.item_ids:
                if line.product_id == self.product_id:
                    price = line.fixed_price
                    unite = line.is_unite
                    break
                if line.product_tmpl_id == self.product_template_id and self.product_uom_qty>=line.min_quantity:
                    price = line.fixed_price
                    unite = line.is_unite
                    break
                    
        self.is_prix_tarif  = price
        self.is_unite_tarif = unite



    # @api.onchange('is_prix_tarif','is_unite_tarif','product_uom_qty')
    # def _onchange_is_prix_tarif(self):
    #     price = 0
    #     if self.is_unite_tarif=="m":
    #         price = self.is_prix_tarif*self.is_longueur
    #     if self.is_unite_tarif=="m2":
    #         price = self.is_prix_tarif*self.is_surface
    #     if self.is_unite_tarif=="m3":
    #         price = self.is_prix_tarif*self.is_volume
    #     if self.is_unite_tarif=="unite":
    #         price = self.is_prix_tarif
    #     self.price_unit = price




    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        self.is_longueur_totale = self.product_uom_qty * self.is_longueur
        self.is_surface_totale  = self.product_uom_qty * self.is_surface
        self.is_volume_total    = self.product_uom_qty * self.is_volume


    @api.onchange('is_longueur_totale')
    def _onchange_is_longueur_totale(self):
        qty = surface = volume = 0
        if self.is_longueur>0:
            qty     = self.is_longueur_totale/self.is_longueur
            surface = self.is_longueur_totale * self.product_id.is_largeur/1000
            volume  = self.is_longueur_totale * self.product_id.is_largeur/1000 * self.product_id.is_epaisseur/1000
        self.product_uom_qty   = qty
        self.is_surface_totale = surface
        self.is_volume_total   = volume


    @api.onchange('is_surface_totale')
    def _onchange_is_surface_totale(self):
        qty = 0
        if self.is_surface>0:
            qty = self.is_surface_totale/self.is_surface
        self.product_uom_qty = qty


    @api.onchange('is_volume_total')
    def _onchange_is_volume_total(self):
        qty = 0
        if self.is_volume>0:
            qty = self.is_volume_total/self.is_volume
        self.product_uom_qty = qty


    def _compute_is_composants(self):
        for obj in self:
            t=[]
            for line in obj.is_composants_ids:
                t.append("<div>- %s x %s</div>"%(line.qty, line.composant_id.name))
            html = "\n".join(t)
            obj.is_composants = html

