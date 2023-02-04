# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = "stock.location"


    def emplacement_origine_charge_action(self):
        filtre=[('quantity','>',0)]
        ids=[]
        lines = self.env['stock.quant'].search(filtre)
        for line in lines:
            if line.location_id.id not in ids:
                ids.append(line.location_id.id )
        view_id = self.env.ref('is_jurabotec.is_stock_location_kanban_view', False)
        return {
            "name": "Origine",
            "view_mode": "kanban",
            "res_model": "stock.location",
            "views": [(view_id.id, 'kanban')],
            "domain": [
                ("id", "in", ids)
            ],
            "type": "ir.actions.act_window",
        }


    def emplacement_charge_action(self):
        for obj in self:
            filtre=[('location_id', '=', obj.id),('quantity','>',0)]
            ids=[]
            lines = self.env['stock.quant'].search(filtre)
            for line in lines:
                if line.lot_id.id not in ids:
                    ids.append(line.lot_id.id )
            view_id = self.env.ref('is_jurabotec.is_stock_lot_kanban_view', False)
            new_context = dict(self.env.context).copy()
            new_context["origine_id"] = obj.id
            return {
                "name": "Origine %s"%(obj.name),
                "view_mode": "kanban",
                "res_model": "stock.lot",
                "views": [(view_id.id, 'kanban')],
                "domain": [
                    ("id", "in", ids)
                ],
                "context": new_context,
                "type": "ir.actions.act_window",
            }


    def destination_charge_action(self):
        for obj in self:
            new_context = dict(self.env.context).copy()
            new_context["destination_id"] = obj.id
            vals={
                "origine_id"    : new_context["origine_id"],
                "destination_id": new_context["destination_id"],
                "lot_id"        : new_context["lot_id"],
                "product_id"    : new_context["product_id"],
                "quantity"      : new_context["quantity"],
            }
            res=self.env['is.deplacement.charge'].create(vals)
            return {
                "name": "Destination %s"%(obj.name),
                "view_mode": "form",
                "res_model": "is.deplacement.charge",
                "res_id": res.id,
                "type": "ir.actions.act_window",
                "context": new_context,
            }




class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.depends('product_id')
    def _compute_qt_lot_emplacement(self):
        for obj in self:
            qt=0
            context = self.env.context
            origine_id = context["origine_id"]
            filtre=[('location_id', '=', origine_id),('quantity','>',0)]
            lines = self.env['stock.quant'].search(filtre)
            for line in lines:
                qt+=line.quantity
            obj.is_qt_lot_emplacement=qt

    is_qt_lot_emplacement = fields.Float("Qt lot dans cet emplacement", compute='_compute_qt_lot_emplacement')


    def deplacer_cette_charge_action(self):
        for obj in self:
            context = self.env.context
            origine_id = context["origine_id"]
            new_context = dict(context).copy()
            new_context["lot_id"]     = obj.id
            new_context["product_id"] = obj.product_id.id
            new_context["quantity"]   = obj.is_qt_lot_emplacement
            view_id = self.env.ref('is_jurabotec.is_stock_location_kanban_view2', False)
            return {
                "name": "Lot %s"%(obj.name),
                "view_mode": "kanban",
                "res_model": "stock.location",
                "views": [(view_id.id, 'kanban')],
                "domain": [
                    ('usage', '=' , 'internal'),
                    ('id'   , '!=', origine_id),
                ],
                "type": "ir.actions.act_window",
                "context": new_context,
            }



class IsDeplacementCharge(models.Model):
    _name='is.deplacement.charge'
    _description="Déplacement charge"
    _order='name'

    origine_id     = fields.Many2one('stock.location' , 'Origine')
    destination_id = fields.Many2one('stock.location' , 'Destination')
    lot_id         = fields.Many2one('stock.lot'      , 'Lot')
    product_id     = fields.Many2one('product.product', 'Article')
    quantity       = fields.Float('Quantité')


    def valider_deplacement_charge_action(self):
        for obj in self:
            context = self.env.context
            line_vals={
                "location_id"     : context["origine_id"],
                "location_dest_id": context["destination_id"],
                "lot_id"          : context["lot_id"],
                "qty_done"        : obj.quantity,
                "product_id"      : context["product_id"],
            }
            move_vals={
                "location_id"     : context["origine_id"],
                "location_dest_id": context["destination_id"],
                "product_uom_qty" : obj.quantity,
                "product_id"      : context["product_id"],
                "name"            : "Tablette",
                #"move_line_ids"   : [[0,False,line_vals]],
            }
            #move=self.env['stock.move'].create(move_vals)
            #TODO : La création du picking est facultative, mais je la garde pour avoir un exemple complet
            filtre=[('code', '=', 'internal')]
            picking_type_id = self.env['stock.picking.type'].search(filtre)[0]
            picking_vals={
                "picking_type_id" : picking_type_id.id,
                "location_id"     : context["origine_id"],
                "location_dest_id": context["destination_id"],
                'move_line_ids'   : [[0,False,line_vals]],
                'move_ids'        : [[0,False,move_vals]],
            }
            picking=self.env['stock.picking'].create(picking_vals)
            picking.action_confirm()
            picking._action_done()

        return self.env['stock.location'].emplacement_origine_charge_action()

