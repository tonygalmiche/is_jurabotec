# -*- coding: utf-8 -*-
from odoo import _, api, fields, models                          # type: ignore
from odoo.tools.float_utils import float_compare, float_is_zero  # type: ignore
from odoo.exceptions import UserError, ValidationError           # type: ignore
import os
import logging
_logger = logging.getLogger(__name__)



# class StockQuant(models.Model):
#     _inherit = "stock.quant"

#     def modifier_charge_action(self):
#         for obj in self:
#             view_id = self.env.ref('is_jurabotec.modifier_charge_stock_quant_form_view', False)
#             return {
#                 "name": obj.lot_id,
#                 "view_mode": "form",
#                 "res_model": "stock.quant",
#                 "views": [(view_id.id, 'form')],
#                 "res_id": obj.id,
#                 "type": "ir.actions.act_window",
#             }


class StockPicking(models.Model):
    _inherit = "stock.picking"
 
    is_bl_fournisseur        = fields.Char("BL fournisseur")
    is_volume_total          = fields.Float(string="Volume total", digits='Volume', compute='_compute_is_volume_total', store=True, readonly=False)
    is_detail_charge         = fields.Boolean("Imprimer le détail des charges")


    @api.depends('move_ids_without_package','is_bl_fournisseur','state')
    def _compute_is_volume_total(self):
        for obj in self:
            volume = 0
            for line in obj.move_ids_without_package:
                if obj.state=='done':
                    qty=line.quantity_done
                else:
                    qty=line.product_uom_qty
                if line.sale_line_id.product_uom_qty>0:
                    volume+=line.sale_line_id.is_volume_total*qty/line.sale_line_id.product_uom_qty
            obj.is_volume_total = round(volume,6)



    def liste_charges_action(self):
        for obj in self:
            ids=[]
            for move in obj.move_ids_without_package:
                for lot in move.lot_ids:
                    ids.append(lot.id)
            return {
                "name": "Charges",
                "view_mode": "tree,form",
                "res_model": "stock.lot",
                "domain": [
                    ("id","in",ids),
                ],
                "type": "ir.actions.act_window",
            }


    def imprime_etiquette_action(self):
        for obj in self:
            ZPL=""
            for line in obj.move_ids_without_package:
                for move_line in line.move_line_ids:
                    if move_line.lot_id:
                        ZPL+=move_line.lot_id.get_zpl()
            path="/tmp/etiquette.zpl"
            fichier = open(path, "w")
            fichier.write(ZPL)
            fichier.close()
            imprimante = "ZD621-1"
            cmd="lpr -h -P"+imprimante+" "+path
            _logger.info(cmd)
            os.system(cmd)


class StockMove(models.Model):
    _inherit = "stock.move"

    is_description_cde = fields.Text('Description commande', compute="_compute_is_description_cde")
    is_lot_id          = fields.Many2one("stock.lot", "Charge", compute="_compute_is_lot_id")


    @api.onchange('move_line_ids.lot_id')
    def _compute_is_lot_id(self):
        for obj in self:
            lot_id=False
            if len(obj.move_line_ids)==1:
                for line in obj.move_line_ids:
                    lot_id = line.lot_id.id
            obj.is_lot_id = lot_id


    @api.onchange('product_id')
    def _compute_is_description_cde(self):
        for obj in self:
            description = obj.description_picking
            if obj.sale_line_id:
                description = obj.sale_line_id.name
            if obj.purchase_line_id:
                description = obj.purchase_line_id.name
            obj.is_description_cde=description








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

    is_fournisseur_id = fields.Many2one('res.partner', 'Fournisseur')
    is_prix_achat     = fields.Float(string="Prix d'achat", digits="Product Price")
    is_valeur         = fields.Float(string="Valeur stock", digits="Product Price", compute='_compute_is_valeur', store=True, readonly=True)
    is_purchase_order_id    = fields.Many2one('purchase.order', string="Cde fournisseur", compute='_compute_is_purchase_order_id', store=False, readonly=True)
    is_detail_charge_client = fields.Char(string="Détail charge Client")
    is_num_interne_client   = fields.Char(string="N° interne Client")
    is_sale_order_id        = fields.Many2one('sale.order', string="Cde client") #, compute='_compute_is_sale_order_id', store=True)
    is_charge_associee_a_commande = fields.Selection([
        ('non', 'Non associée'), 
        ('oui', 'Associée'),
    ], string='Charge associée à une commande', group_expand='_group_expand_states', default='non')


    def write(self, vals):
        charge_associee = vals.get('is_charge_associee_a_commande',False)
        if charge_associee:
            order_id=False
            if charge_associee=='oui':
                order_id = self._context.get('is_sale_order_id',False)
            vals['is_sale_order_id'] = order_id
        res = super(StockLot, self).write(vals)
        return res


    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).is_charge_associee_a_commande.selection]


    @api.depends('purchase_order_ids')
    def _compute_is_purchase_order_id(self):
        for obj in self:
            order_id=False
            for line in obj.purchase_order_ids:
                order_id = line.id
            obj.is_purchase_order_id = order_id


    @api.depends('is_prix_achat','product_qty')
    def _compute_is_valeur(self):
        for obj in self:
            obj.is_valeur = obj.product_qty*obj.is_prix_achat


    @api.depends('product_id')
    def _compute_qt_lot_emplacement(self):
        for obj in self:
            qt=0
            context = self.env.context
            origine_id = context.get("origine_id", False)
            product_id = obj.product_id.id
            if origine_id:
                filtre=[
                    ('lot_id'     , '=', obj.id),
                    ('product_id' , '=', product_id),
                    ('location_id', '=', origine_id),
                    ('quantity'   , '>', 0),
                ]
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


    def init_prix_achat_action(self):
        for obj in self:
            for order in obj.purchase_order_ids:
                for line in order.order_line:
                    if obj.product_id==line.product_id:
                        obj.is_fournisseur_id = order.partner_id.id
                        if line.price_unit>0:
                            obj.is_prix_achat = line.price_unit


    @api.model
    def init_prix_achat_ir_cron(self):
        self.env['stock.lot'].search([]).init_prix_achat_action()
        return True


    def get_zpl(self):
        for obj in self:
            designation = obj.product_id.name_get()[0][1]
            fournisseur = obj.is_fournisseur_id.name
            longueur    = round(obj.product_id.is_longueur,1)
            quantite    = round(obj.product_qty)
            ZPL="""
^XA
^CI28         ^FX UTF-8

^FWR          ^FX Rotation à 90°
^CF0,60       ^FX Taille de police

^BY7,4,200                        ^FX Dimensions du code barre
^FO500,50^BC^FD%s^FS              ^FX Code barre avec texte dessous

^CF0,70                                                                         ^FX Taille de police
^FO310,50^FD%s^FS   ^FX Postion x,y et texte

^CF0,60                                                                         ^FX Taille de police
^FO230,50^FD%s^FS   ^FX Postion x,y et texte

^CF0,180                                                                        ^FX Taille de police
^FO10,50^FD%sm ^FS   ^FX Postion x,y et texte

^CF0,180                                                                        ^FX Taille de police
^FO10,800^FD%s^FS   ^FX Postion x,y et texte

^XZ
            """%(obj.name,designation,fournisseur,longueur,quantite)
            _logger.info(ZPL)
            return ZPL


    def imprime_etiquette_action(self):
        for obj in self:
            ZPL = obj.get_zpl()
            path="/tmp/etiquette.zpl"
            fichier = open(path, "w")
            fichier.write(ZPL)
            fichier.close()
            imprimante = "ZD621-1"
            cmd="lpr -h -P"+imprimante+" "+path
            _logger.info(cmd)
            os.system(cmd)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    is_cout          = fields.Float(string="Coût"      , compute='_compute_is_cout', readonly=True, store=False, digits="Product Price", help="Coût pour valorisation stock (Prix achat du lot ou prix dans fiche article)")
    is_cout_total    = fields.Float(string="Coût total", compute='_compute_is_cout', readonly=True, store=False, digits="Product Price", help="Coût total pour valorisation stock")
    is_sale_order_id = fields.Many2one(related="lot_id.is_sale_order_id")


    def _compute_is_cout(self):
        for obj in self:
            cout = obj.lot_id.is_prix_achat
            if not cout:
                cout = obj.product_id.standard_price
            obj.is_cout = cout
            obj.is_cout_total = obj.quantity * cout


    def deplacer_quant_action(self):
        for obj in self:
            context = self.env.context
            origine_id = obj.location_id.id
            new_context = dict(context).copy()
            new_context["origine_id"] = origine_id
            new_context["lot_id"]     = obj.lot_id.id
            new_context["product_id"] = obj.product_id.id
            new_context["quantity"]   = obj.quantity
            view_id = self.env.ref('is_jurabotec.is_stock_location_kanban_view2', False)
            return {
                "name": "Lot %s"%(obj.lot_id.name),
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






    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            #if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
            #    raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            #if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
            #    raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants




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


class IsCreationCharge(models.Model):
    _name='is.creation.charge'
    _description="Création charge"
    _order='id desc'
    _rec_name = "lot_id"

    def _get_destination_id(self):
        filtre=[('code','=','incoming')]
        lines = self.env['stock.picking.type'].search(filtre, limit=1)
        destination_id = False
        for line in lines:
            destination_id = line.default_location_dest_id.id
        return destination_id


    product_id     = fields.Many2one('product.product', 'Article'    , required=True)
    quantity       = fields.Float('Quantité'                         , required=True, digits='Product Unit of Measure')
    destination_id = fields.Many2one('stock.location' , 'Destination', required=True, default=_get_destination_id, domain=[('usage','=','internal')])
    lot_id         = fields.Many2one('stock.lot'      , 'Lot créé'   , readonly=True)


    def creer_charge_action(self):
        for obj in self:
            vals={
                'product_id': obj.product_id.id,
                'company_id': self.env.user.company_id.id,
                'name'      : self.env['ir.sequence'].next_by_code('stock.lot.serial'),
            }
            lot = self.env['stock.lot'].create(vals)
            obj.lot_id = lot.id


            #** Création stock.move et stock.move.line ************************
            location_id = 14 # Inventory adjustment
            location_dest_id = obj.destination_id.id


            line_vals={
                "location_id"     : location_id,
                "location_dest_id": location_dest_id,
                "lot_id"          : lot.id,
                "qty_done"        : obj.quantity,
                "product_id"      : obj.product_id.id,
            }
            move_vals={
                #"production_id"   : production_id, # Si j'indique ce champ avant la création du lot, j'ai message => La quantité de xxx débloquée ne peut pas être supérieure à la quantité en stock
                "location_id"     : location_id,
                "location_dest_id": location_dest_id,
                "product_uom_qty" : obj.quantity,
                "product_id"      : obj.product_id.id,
                "name"             : "Création charge %s"%(lot.name),
                "move_line_ids"   : [[0,False,line_vals]],
            }
            move=self.env['stock.move'].with_context({}).create(move_vals) # Il faut effacer le context, sinon erreur avec le champ product_qty
            move._action_done()
            #move.production_id = production_id # Permet d'associer le mouvement à l'ordre de fabrication après sa création
            #******************************************************************





#    def action_generate_serial(self):
#         self.ensure_one()
#         self.lot_producing_id = self.env['stock.lot'].create({
#             'product_id': self.product_id.id,
#             'company_id': self.company_id.id,
#             'name': self.env['stock.lot']._get_next_serial(self.company_id, self.product_id) or 
# self.env['ir.sequence'].next_by_code('stock.lot.serial'),
#         })
#         if self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids:
#             self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids.lot_id = self.lot_producing_id
#         if self.product_id.tracking == 'serial':
#             self._set_qty_producing()

