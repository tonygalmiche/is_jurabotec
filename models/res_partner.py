
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_code_comptable_fournisseur = fields.Char("Code comptable fournisseur")
    is_code_comptable_client      = fields.Char("Code comptable client")
