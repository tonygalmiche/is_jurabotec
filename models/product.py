# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from random import randint
import os
import base64


class IsBois(models.Model):
    _name='is.bois'
    _description = "Bois"
    _order='sequence'

    name     = fields.Char("Bois", required=True)
    sequence = fields.Integer("Ordre")
    active   = fields.Boolean("Actif", default=True)
    


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
    is_largeur          = fields.Float("Largeur (mm)"  , digits='Product Unit of Measure')
    is_epaisseur        = fields.Float("Epaisseur (mm)", digits='Product Unit of Measure')
    is_ref_plan         = fields.Char("Référence plan")
    is_plan_ids         = fields.Many2many('ir.attachment', 'product_template_is_plan_rel', 'product_id', 'attachment_id', 'Plan')


    def import_plan_action(self):
        plans = {}
        dir_path = "/home/odoo/plans"
        #dir_path = "/media/sf_dev_odoo/16.0/jurabotec/plans/"
        for filename in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, filename)):
                end = filename.find("-")
                if end>0:
                    ref = filename[0:end]
                    plans[ref]=filename
        for obj in self:
            if len(obj.is_plan_ids)==0:
                if obj.is_ref_plan in plans:
                    filename = plans[obj.is_ref_plan]
                    path = os.path.join(dir_path, filename)    
                    r = open(path,'rb').read()
                    r = base64.b64encode(r)
                    vals = {
                        'name':        filename,
                        'type':        'binary',
                        'res_model':   "product.template",
                        'res_id':      obj.id,
                        'datas':       r,
                    }
                    attachment = self.env['ir.attachment'].create(vals)
                    obj.is_plan_ids=[(6,0,[attachment.id])]


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
                    except:
                        longeur = 0
            obj.is_longueur = longeur
            obj.is_surface  = longeur*obj.is_largeur/1000
            obj.is_volume   = longeur*obj.is_largeur*obj.is_epaisseur/1000/1000

    is_longueur = fields.Float("Longueur (m)", digits='Product Unit of Measure', compute='_compute_longueur')
    is_surface  = fields.Float("Surface (m2)", digits='Product Unit of Measure', compute='_compute_longueur')
    is_volume   = fields.Float("Volume (m3) ", digits='Volume'                 , compute='_compute_longueur')
