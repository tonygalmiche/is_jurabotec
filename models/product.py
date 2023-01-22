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
    is_largeur          = fields.Integer("Largeur")
    is_epaisseur        = fields.Integer("Epaisseur")


#     • Désignation de base
#     • Commentaire
#     • Longueur => Permettra de distinguer les variantes des articles



# La désignation complète sera la concaténation de ces champs : 
#     • Désignation de base
#     • Bois : Liste de choix (ex : Redwoo)
#     • Qualité : Liste de choix multiples (ex : S/F)
# L’article de base n’aura pas de longueur et il sera utilisé dans les contrats avec les fournisseurs
# La longueur sera indiquée dans la variante de l’article (Une variante par longueur)
# L’unité par défaut sera la pièce.