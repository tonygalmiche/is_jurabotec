# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from random import randint

class IsBois(models.Model):
    _name='is.bois'
    _description = "Bois"

    name = fields.Char("Bois", required=True)

class IsQualiteBois(models.Model):
    _name='is.qualite.bois'
    _description = "Qualité bois"

    def _get_default_color(self):
        return randint(1, 11)

    name  = fields.Char("Qualité bois", required=True)
    color = fields.Integer("Couleur", default=_get_default_color)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_bois_id    = fields.Many2one('is.bois', 'Bois')
    is_qualite_bois_ids = fields.Many2many('is.qualite.bois', column1='product_id', column2='qualite_id', string='Qualité bois')
    is_largeur          = fields.Float("Largeur (mm)")
    is_epaisseur        = fields.Float("Epaisseur (mm)")


class ProductProduct(models.Model):
    _inherit = "product.product"
 
    @api.depends('product_template_variant_value_ids','is_largeur','is_epaisseur')
    def _compute_longueur(self):
        for obj in self:
            longeur = 0
            for line in obj.product_template_variant_value_ids:
                if line.attribute_line_id.attribute_id.name=="Longueur":
                    val = line.product_attribute_value_id.name
                    try:
                        longeur = float(val)
                    except TypeError:
                        longeur = 0
            obj.is_longueur = longeur
            obj.is_surface  = longeur*obj.is_largeur/1000
            obj.is_volume   = longeur*obj.is_largeur*obj.is_epaisseur/1000/1000

    is_longueur = fields.Float("Longueur (m)", compute='_compute_longueur')
    is_surface  = fields.Float("Surface (m2)", compute='_compute_longueur')
    is_volume   = fields.Float("Volume (m3) ", compute='_compute_longueur', digits=(16, 4))
