# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from random import randint
import os
import base64
from odoo.osv import expression


class IsBois(models.Model):
    _name='is.bois'
    _description = "Bois"
    _order='sequence'

    name         = fields.Char("Bois", required=True)
    sequence     = fields.Integer("Ordre")
    active       = fields.Boolean("Actif", default=True)
    prix_revient = fields.Float(string="Prix de revient (€/litre)", digits="Product Price")


class IsQualiteBois(models.Model):
    _name='is.qualite.bois'
    _description = "Qualité bois"

    def _get_default_color(self):
        return randint(1, 11)

    name  = fields.Char("Qualité bois", required=True)
    color = fields.Integer("Couleur", default=_get_default_color)


class IsCalculateurOperation(models.Model):
    _name='is.calculateur.operation'
    _description = "Opérations du calculateur"

    name         = fields.Char("Opération", required=True)
    prix_revient = fields.Float(string="Prix de revient", digits="Product Unit of Measure", required=True)
    unite = fields.Selection([
            ('litre', 'litre'),
            ('ml'   , 'ml'),
        ], "Unité du prix de revient", default='litre', required=True)
    active = fields.Boolean("Actif", default=True)


class IsProductTemplateCalculateurOperation(models.Model):
    _name='is.product.template.calculateur.operation'
    _description = "Opérations du calculateur de la fiche article"


    @api.depends('prix_revient','unite','product_id.is_litre_metre')
    def _compute_montant(self):
        for obj in self:
            montant=0
            if obj.unite=="ml":
                montant=obj.prix_revient
            if obj.unite=="litre":
                montant=obj.prix_revient*obj.product_id.is_litre_metre
            obj.montant=montant


    product_id   = fields.Many2one('product.template', 'Article', required=True, ondelete='cascade')
    sequence     = fields.Integer("Ordre")
    operation_id = fields.Many2one('is.calculateur.operation', 'Opération', required=True)
    prix_revient = fields.Float(related="operation_id.prix_revient")
    unite        = fields.Selection(related="operation_id.unite")
    montant      = fields.Float(string="Montant", digits="Product Price", compute='_compute_montant', store=True)


class ProductTemplate(models.Model):
    _inherit = "product.template"


    @api.depends('is_largeur','is_epaisseur')
    def _compute_is_litre_metre(self):
        for obj in self:
            obj.is_litre_metre = obj.is_largeur*obj.is_epaisseur/1000  # Épaisseur x Largeur / 1000


    @api.depends('is_litre_metre','is_prix_revient_bois')
    def _compute_is_montant_bois(self):
        for obj in self:
            obj.is_montant_bois = obj.is_litre_metre*obj.is_prix_revient_bois


    @api.depends('is_montant_bois','is_operation_ids')
    def _compute_is_prix_revient(self):
        for obj in self:
            v=0
            for line in obj.is_operation_ids:
                v+=line.montant
            v+=obj.is_montant_bois
            obj.is_prix_revient = v


    is_bois_id           = fields.Many2one('is.bois', 'Bois')
    is_prix_revient_bois = fields.Float("Prix de revient du bois", related="is_bois_id.prix_revient")
    is_montant_bois      = fields.Float("Montant bois", compute='_compute_is_montant_bois', store=True)
    is_qualite_bois_ids  = fields.Many2many('is.qualite.bois', column1='product_id', column2='qualite_id', string='Qualité bois')
    is_largeur           = fields.Float("Largeur (mm)"  , digits='Product Unit of Measure')
    is_epaisseur         = fields.Float("Epaisseur (mm)", digits='Product Unit of Measure')
    is_longueur_modele   = fields.Float("Longueur modèle (m)", digits='Product Unit of Measure', help="Ce champ est utilisé si la longueure n'est pas indiquée dans la variante")
    is_ref_plan          = fields.Char("Référence plan")
    is_plan_ids          = fields.Many2many('ir.attachment', 'product_template_is_plan_rel', 'product_id', 'attachment_id', 'Plan')
    is_fds_ids           = fields.Many2many('ir.attachment', 'product_template_is_fds_rel' , 'product_id', 'attachment_id', 'FDS', help="Fiche de sécurité")
    is_litre_metre       = fields.Float("L/m ", digits='Product Unit of Measure', compute='_compute_is_litre_metre', store=True, help="Litre / mètre => Unité fictive pour faciliter le calcul des devis")
    is_operation_ids     = fields.One2many('is.product.template.calculateur.operation', 'product_id', 'Opérations')
    is_prix_revient      = fields.Float("Prix de revient (€/ml)", compute='_compute_is_prix_revient', store=False, help="Montant des opérations + Montant bois")
    is_cout_fixe         = fields.Float("Coût fixe", help="Coût fixe ajouté aux variantes")


    def init_cout_action(self):
        for obj in self:
            obj.product_variant_ids.init_cout_action()


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
 
    is_longueur              = fields.Float("Longueur (m)", digits='Product Unit of Measure', compute='_compute_longueur')
    is_surface               = fields.Float("Surface (m2)", digits='Product Unit of Measure', compute='_compute_longueur')
    is_volume                = fields.Float("Volume (m3) ", digits='Volume'                 , compute='_compute_longueur')
    is_prix_revient_variante = fields.Float("Prix de revient variante"                      , compute='_compute_is_prix_revient_variante')
    is_volume_stock          = fields.Float("Volume en stock (m3) ", digits='Volume'        , compute='_compute_is_volume_stock')


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
            if not longeur and obj.is_longueur_modele:
                longeur = obj.is_longueur_modele
            obj.is_longueur    = longeur
            obj.is_surface     = longeur*obj.is_largeur/1000
            obj.is_volume      = longeur*obj.is_largeur*obj.is_epaisseur/1000/1000


    @api.depends('is_prix_revient','is_longueur','is_cout_fixe')
    def _compute_is_prix_revient_variante(self):
        for obj in self:
            obj.is_prix_revient_variante=obj.is_prix_revient*obj.is_longueur+obj.is_cout_fixe


    def _compute_is_volume_stock(self):
        for obj in self:
            obj.is_volume_stock = obj.is_volume * obj.qty_available


    def init_cout_action(self):
        for obj in self:
            obj.standard_price = obj.is_prix_revient_variante


    def liste_charges_action(self):
        for obj in self:
            view_id = self.env.ref('is_jurabotec.charge_stock_quant_kanban_view', False)
            #new_context = dict(self.env.context).copy()
            #new_context["origine_id"] = obj.id
            return {
                "name": obj.name,
                "view_mode": "kanban",
                "res_model": "stock.quant",
                "views": [(view_id.id, 'kanban')],
                "domain": [
                    ("product_id", "=", obj.id),
                    ('location_id.usage','=', 'internal'),
                    ('quantity','>', 0),
                ],
                #"context": new_context,
                "type": "ir.actions.act_window",
            }


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        product_ids=[]
        contrat_id = self._context.get('contrat_id')
        if contrat_id:
            lines = self.env['is.contrat.fournisseur.ligne'].search([('contrat_id','=',contrat_id)])
            for line in lines:
                for product in line.product_id.product_variant_ids:
                    product_ids.append(product.id)
        else:
            product_ids = super()._name_search(name, args, operator, limit, name_get_uid)
        return product_ids





class ProductTemplateAttributeValue(models.Model):
    """Materialized relationship between attribute values
    and product template generated by the product.template.attribute.line"""
    _inherit = "product.template.attribute.value"


    #TODO : Permet d'ajouter l'unité 'M' aux attributs des longeurs
    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        ids=[]
        for ptav in ptavs:
            name = ptav.name
            if ptav.attribute_id.name=="Longueur":
                try:
                    longeur = float(name)
                except:
                    longeur = 0
                if longeur>0:
                    name="%sM"%name
            ids.append(name)
        res = ", ".join(ids)
        return res