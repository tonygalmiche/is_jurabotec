# -*- coding: utf-8 -*-
from odoo import models, fields, api   # type: ignore
from odoo.exceptions import UserError  # type: ignore
import time

class IsScanInventaire(models.TransientModel):
    _name = 'is.scan.inventaire'
    _description = 'Inventaire par scan'

    barcode_input = fields.Char(string='Input utilisé par le widget pour récupérer les données du scan')
    barcode_scan  = fields.Char(string='Résultat du scan')
    #test_onchange = fields.Char(string='Champ de test du onchange')


    @api.model
    def on_barcode_scanned(self, barcode):
        """
            Méthode appelée par le widget OWL après le scan pour retourner les valeurs
        """
        if not barcode:
            raise UserError("Le code-barres est vide. Veuillez scanner une étiquette.")

        existing_product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        # if existing_product:
        #     raise UserError(f"Un produit avec ce code-barres existe déjà : {existing_product.display_name}. Vous ne pouvez pas créer un doublon.")

        print("TEST",barcode,existing_product)

        return {'barcode': "%s scanné"%barcode}
