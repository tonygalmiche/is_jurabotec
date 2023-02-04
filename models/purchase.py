# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IsContratFournisseurLigne(models.Model):
    _name='is.contrat.fournisseur.ligne'
    _description = "Lignes contrat fournisseur"


    @api.depends('qt_prevue','prix_achat')
    def _compute_montant(self):
        for obj in self:
            montant = 0
            if obj.qt_prevue and obj.prix_achat:
                montant =  obj.qt_prevue * obj.prix_achat
            obj.montant = montant


    contrat_id   = fields.Many2one('is.contrat.fournisseur', 'Contrat', required=True, ondelete='cascade')
    product_id   = fields.Many2one('product.template', 'Article', required=True)
    qt_prevue    = fields.Float(string="Quantité prévue", digits='Product Unit of Measure', required=True)
    prix_achat   = fields.Float(string="Prix d'achat"   , digits='Product Unit of Measure', required=True)
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

    is_contrat_id = fields.Many2one('is.contrat.fournisseur', 'Contrat')


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


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
