# -*- coding: utf-8 -*-
from odoo import models,fields,api


class AccountMove(models.Model):
    _inherit = "account.move"

    is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)



    def mise_en_page_hekipia_action(self):
        for obj in self:
            print(obj)
            domain=[
                ('move_id','=',obj.id),
                ('display_type', 'in', ('product', 'line_section', 'line_note')),
            ]
            lines= self.env['account.move.line'].search(domain,order="sequence,id")
            for line in lines:
                print(line.id,line.sequence,line.product_id,line.name[:20],line.sale_line_ids)
                #for order_line in line.sale_line_ids

                moves= self.env['stock.move'].search(domain,order="sequence,id")


    

# stock.move : 
# - account_move_ids => Lien vers account.move
# - sale_line_id => Lien vers sale.order.line

# account.move.line : 
# - sale_line_ids => Lien vers sale.order.line


