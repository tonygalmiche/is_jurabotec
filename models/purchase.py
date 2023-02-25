# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IsContratFournisseurLigne(models.Model):
    _name='is.contrat.fournisseur.ligne'
    _description = "Lignes contrat fournisseur"
    _rec_name = "id"

    @api.depends('qt_prevue','prix_achat')
    def _compute_montant(self):
        for obj in self:
            montant = 0
            if obj.qt_prevue and obj.prix_achat:
                montant =  obj.qt_prevue * obj.prix_achat
            obj.montant = montant


    def _compute_qt_commandee(self):
        for obj in self:
            filtre=[
                ('is_contrat_id', '=', obj.contrat_id.id),
                ('state','in',["purchase"]),
            ]
            orders = self.env['purchase.order'].search(filtre)
            qt = 0
            for order in orders:
                for line in order.order_line:
                    if line.product_id.product_tmpl_id==obj.product_id:
                        qt+=line.is_volume_total
            obj.qt_commandee = qt


    contrat_id   = fields.Many2one('is.contrat.fournisseur', 'Contrat', required=True, ondelete='cascade')
    product_id   = fields.Many2one('product.template', 'Article', required=True)
    qt_prevue    = fields.Float(string="Quantité prévue"   , digits='Product Unit of Measure', required=True)
    qt_commandee = fields.Float(string="Quantité commandée", digits='Product Unit of Measure', compute='_compute_qt_commandee')
    prix_achat   = fields.Float(string="Prix d'achat"      , digits='Product Unit of Measure', required=True)
    unite = fields.Selection([
        ('m' , 'm'),
        ('m2', 'm2'),
        ('m3', 'm3'),
    ], "Unité", default='m3', required=True)
    montant = fields.Float("Montant", compute='_compute_montant', store=True, readonly=True)


class IsContratFournisseur(models.Model):
    _name='is.contrat.fournisseur'
    _description = "Contrat fournisseur"
    _order = "name desc"


    @api.depends('ligne_ids')
    def _compute_montant(self):
        for obj in self:
            montant = 0
            for line in obj.ligne_ids:
                montant+=line.montant
            obj.montant = montant


    name          = fields.Char("N°contrat", readonly=True)
    partner_id    = fields.Many2one('res.partner', 'Fournisseur', required=True)
    date_creation = fields.Date("Date de création", readonly=True, default=lambda *a: fields.datetime.now())
    commentaire   = fields.Text("Commentaire")
    state = fields.Selection([
        ('en_cours', 'En cours'),
        ('solde'   , 'Soldé'),
    ], "Etat", default='en_cours')
    ligne_ids = fields.One2many('is.contrat.fournisseur.ligne', 'contrat_id', 'Lignes', copy=True)
    montant = fields.Float("Montant", compute='_compute_montant', store=True, readonly=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.contrat.fournisseur')
        return super().create(vals_list)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_contrat_id = fields.Many2one('is.contrat.fournisseur', 'Contrat', index=True)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_ligne_contrat_id = fields.Many2one('is.contrat.fournisseur.ligne', 'Ligne contrat')
    is_qt_contrat       = fields.Float(string="Qt contrat", digits='Product Unit of Measure')
    is_prix_contrat     = fields.Float(string="Prix contrat"   , digits='Product Unit of Measure')
    is_unite_contrat    = fields.Selection([
        ('m' , 'm'),
        ('m2', 'm2'),
        ('m3', 'm3'),
    ], "Unité contrat")
    is_volume       = fields.Float(string="Volume"      , digits='Volume', related="product_id.is_volume", readonly=True)
    is_volume_total = fields.Float(string="Volume total", digits='Volume', compute='_compute_is_volume_total')
    is_product_ids  = fields.Many2many('product.product', 'is_purchase_order_line_product_ids', 'line_id', 'product_id', store=False, readonly=True, compute='_compute_is_product_ids', string="Articles autorisés")


    @api.depends('order_id','order_id.is_contrat_id','order_id.partner_id')
    def _compute_is_product_ids(self):
        for obj in self:
            ids=[]
            if obj.order_id.partner_id:
                if obj.order_id.is_contrat_id:
                    for line in obj.order_id.is_contrat_id.ligne_ids:
                        for product in line.product_id.product_variant_ids:
                            ids.append(product.id)
                else:
                    filtre=[
                        ('partner_id', '=', obj.order_id.partner_id.id)
                    ]
                    lines = self.env['product.supplierinfo'].search(filtre)
                    for line in lines:
                        for product in line.product_tmpl_id.product_variant_ids:
                            ids.append(product.id)
            obj.is_product_ids= [(6, 0, ids)]


    def _compute_price_unit_and_date_planned_and_name(self):
        super(PurchaseOrderLine, self)._compute_price_unit_and_date_planned_and_name()
        price_unit = False
        if self.product_id:
            for line in self.order_id.is_contrat_id.ligne_ids:
                if line.product_id == self.product_id.product_tmpl_id:
                    if line.unite=="m3":
                        price_unit = line.prix_achat*self.product_id.is_volume
        if price_unit:
            self.price_unit = price_unit


    @api.depends('is_volume','product_qty')
    def _compute_is_volume_total(self):
        for obj in self:
            obj.is_volume_total = obj.product_qty*obj.is_volume


    @api.onchange('product_id')
    def _onchange_product_id_contrat(self):
        self.is_ligne_contrat_id = False
        self.is_qt_contrat       = False
        self.is_prix_contrat     = False
        self.is_unite_contrat    = False
        if self.product_id:
            for line in self.order_id.is_contrat_id.ligne_ids:
                if line.product_id == self.product_id.product_tmpl_id:
                    self.is_ligne_contrat_id = line.id
                    self.is_qt_contrat       = line.qt_prevue
                    self.is_prix_contrat     = line.prix_achat
                    self.is_unite_contrat    = line.unite
                    break
