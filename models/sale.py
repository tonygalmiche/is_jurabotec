# -*- coding: utf-8 -*-
from itertools import groupby
from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.fields import Command
from math import *

class IsSaleOrderColis(models.Model):
    _name='is.sale.order.colis'
    _description = "Colis des commandes"
    _order='sequence'

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    sequence     = fields.Integer("Ordre")
    name         = fields.Char("Colis", required=True)
    colisage_ids = fields.One2many('is.sale.order.colisage.composant', 'colis_id', 'Colisage')


    def imprimer_fiche_colisage_action(self):
        for obj in self:
            report=self.env.ref('is_jurabotec.is_sale_order_colis_reports')
            return report.report_action([obj.id])


    def repartir_colis_action(self):
        for obj in self:

            #** Test si supérieur à 8
            for line in obj.colisage_ids:
                if line.qty_cde<=8:
                    raise ValidationError("La quantité commandée doit-être supérieure à 8")
                if line.qty!=(line.qty_cde*line.qty_bom):
                    raise ValidationError("Une répartition a déjà été faite")
                
            #** Recherche qty mini
            qty_mini=False
            for line in obj.colisage_ids:
                if line.qty_cde>0:
                    if not qty_mini:
                        qty_mini = line.qty_cde
                    if qty_mini>line.qty_cde:
                        qty_mini = line.qty_cde
            repartition=ceil(qty_mini/8)
            if repartition>1:

                #Liste des colis
                dict_colis={}
                name=obj.name
                for i in range(0, repartition):
                    if i==0:
                        dict_colis[i]=obj
                        colis = obj
                    else:
                        colis = obj.copy()
                    colis.name = "%s.%s"%(name,(i+1))
                    dict_colis[i]=colis
    
                for line in obj.colisage_ids:
                    reste = line.qty_cde
                    if line.qty_cde>0:

                        for i in range(0, repartition):
                            qty=ceil(line.qty_cde/repartition)
                            reste = reste - qty
                            if reste<0:
                                qty=qty+reste
                            if i==0:
                                line.qty=qty*line.qty_bom
                            else:
                                new_line = line.copy()
                                new_line.qty = qty*line.qty_bom
                                new_line.colis_id = dict_colis[i].id


    def lignes_colis_action(self):
        for obj in self:
            return {
                "name": obj.name,
                "view_mode": "tree,form",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("colis_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_colis_action(self):
        for obj in self:
            res= {
                'name': obj.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res






class IsSaleOrderColisageComposant(models.Model):
    _name='is.sale.order.colisage.composant'
    _description = "Colisage des composants"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    colis_id     = fields.Many2one('is.sale.order.colis', 'Colis', group_expand='_group_expand_colis_id', required=True)
    #product_id   = fields.Many2one('product.product', 'Article')
    product_id   = fields.Many2one("product.product", string="Article", related="sale_line_id.product_id", readonly=True)
    composant_id = fields.Many2one('product.product', 'Composant')
    qty          = fields.Float(string='Quantité', digits='Product Unit of Measure')
    qty_bom      = fields.Float(string='Qt nomenclature', digits='Product Unit of Measure')
    qty_cde      = fields.Float(related='sale_line_id.product_uom_qty')
    sale_line_id = fields.Many2one('sale.order.line', 'Ligne de commande', required=True)
    colis_ids    = fields.Many2many('is.sale.order.colis', 'is_sale_order_line_colis_ids', 'line_id', 'colis_id', store=False, readonly=True, compute='_compute_colis_ids', string="Colis autorisés")


    @api.depends('colis_id')
    def _compute_colis_ids(self):
        for obj in self:
            ids=[]
            for colis in obj.order_id.is_colis_ids:
                ids.append(colis.id)
            obj.colis_ids= [(6, 0, ids)]


    @api.model
    def _group_expand_colis_id(self, stages, domain, order):
        # # retrieve team_id from the context and write the domain
        # # - ('id', 'in', stages.ids): add columns that should be present
        # # - OR ('fold', '=', False): add default columns that are not folded
        # # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        # team_id = self._context.get('default_team_id')
        # if team_id:
        #     search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        # else:
        #     search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # # perform search
        # stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        colis = self.env['is.sale.order.colis'].search([])
        colis = stages.order_id.is_colis_ids
        return colis


    def dupliquer_colis_action(self):
        for obj in self:
            res=obj.copy()
            res.qty=0


    def voir_colis_action(self):
        for obj in self:
            res= {
                'name': obj.colis_id.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.colis_id.id,
                'type': 'ir.actions.act_window',
            }
            return res




           

class sale_order(models.Model):
    _inherit = "sale.order"

    is_delai             = fields.Date('Délai')
    is_colis_ids         = fields.One2many('is.sale.order.colis'             , 'order_id', 'Colis')
    is_colisage_ids      = fields.One2many('is.sale.order.colisage.composant', 'order_id', 'Colisage')
    is_num_cde_client    = fields.Char('N° commande client')
    is_detail_composants = fields.Boolean('Imprimer le détail des composants', default=False)
    is_devis_id          = fields.Many2one('sale.order', "Devis d'origine", copy=False, readonly=True)
    is_volume_total      = fields.Float(string="Volume total", digits='Volume', compute='_compute_is_volume_total', store=True, readonly=False)


    @api.depends('order_line','order_line.product_uom_qty')
    def _compute_is_volume_total(self):
        for obj in self:
            volume = 0
            for line in obj.order_line:
                volume+=line.is_volume_total
            obj.is_volume_total = volume


    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Create invoice(s) for the given Sales Order(s).

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :returns: created invoices
        :rtype: `account.move` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """

        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.

        #** Permet de trier les commandes par ordre de création (id) **********
        ids=[]
        for order in self:
            ids.append(order.id)
        filtre=[('id', 'in', ids)]
        orders = self.env['sale.order'].search(filtre,order="id")
        #**********************************************************************

        for order in orders:
            invoice_line_vals = []
            #** Recherche des livraions à facturer pour indiquer le BL ******** 
            pickings=[]
            for line in order.order_line:
                if line.qty_invoiced<line.qty_delivered:
                    for move in line.move_ids:
                        if move.state=='done' and move.picking_id not in pickings:
                            pickings.append(move.picking_id)
            #******************************************************************

            #** Ajout de la section de la commande  sur la facutre ************
            list=[]
            list.append("Commande : %s"%order.name)
            if order.client_order_ref:
                list.append("Référence client : %s"%order.client_order_ref)
            if order.is_num_cde_client:
                list.append("N° commande client : %s"%order.is_num_cde_client)
            for picking in pickings:
                list.append("Livraion : %s"%picking.name)
            name = " - ".join(list)
            section_vals = {
                'display_type': 'line_section',
                'name': name,
                'sequence': invoice_item_sequence,
                'product_id': False,
                'product_uom_id': False,
                'quantity': 0,
                'discount': 0,
                'price_unit': 0,
                'account_id': False,
            }
            invoice_line_vals.append(Command.create(section_vals))
            invoice_item_sequence += 1
            #******************************************************************

            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)
            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)
            if not any(not line.display_type for line in invoiceable_lines):
                continue
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        Command.create(
                            order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                        ),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    Command.create(
                        line._prepare_invoice_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
            raise UserError(self._nothing_to_invoice_error_message())

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                'mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        return moves


    def convertir_en_commande_action(self):
        for obj in self:
            copy = obj.copy()
            copy.is_devis_id = obj.id
            res= {
                'name': copy.name,
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': copy.id,
                'type': 'ir.actions.act_window',
            }
            return res


    def colisage_action(self):
        for obj in self:
            if len(obj.is_colisage_ids)==0 and len(obj.is_colis_ids)>0:
                for line in obj.order_line:
                    filtre=[
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                        ('type'           , '=', 'commande'),
                    ]
                    boms = self.env['mrp.bom'].search(filtre,limit=1)
                    if len(boms)>0:
                        for bom_line in boms[0].bom_line_ids:
                            vals={
                                "colis_id"    : obj.is_colis_ids[0].id,
                                "order_id"    : obj.id,
                                "composant_id": bom_line.product_id.id,
                                "qty"         : line.product_uom_qty*bom_line.product_qty,
                                "qty_bom"     : bom_line.product_qty,
                                "sale_line_id": line.id,
                            }
                            res = self.env['is.sale.order.colisage.composant'].create(vals)
                    else:
                        vals={
                            "colis_id": obj.is_colis_ids[0].id,
                            "order_id": obj.id,
                            "composant_id": line.product_id.id,
                            "qty": line.product_uom_qty,
                            "sale_line_id": line.id,
                        }
                        res = self.env['is.sale.order.colisage.composant'].create(vals)
            return {
                "name": "Colisage des composants %s"%(obj.name),
                "view_mode": "kanban,tree,form",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }


    def liste_colis_action(self):
        for obj in self:
           return {
                "name": "Colis %s"%(obj.name),
                "view_mode": "tree,form",
                "res_model": "is.sale.order.colis",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_composants     = fields.Html(string='Composants', compute='_compute_is_composants')
    is_composants_ids = fields.One2many('is.sale.order.colisage.composant', 'sale_line_id', 'Lignes des composants')
    is_prix_tarif  = fields.Float(string="Prix tarif", digits='Product Unit of Measure', help="Tarif de la liste de prix")
    is_unite_tarif = fields.Selection([
        ('m'    , 'm'),
        ('m2'   , 'm2'),
        ('m3'   , 'm3'),
        ('unite', 'Unité'),
    ], "Unité", help="Unité de la liste de prix")
    is_longueur        = fields.Float(string="Longueur",        digits='Product Unit of Measure', related="product_id.is_longueur", readonly=True)
    is_longueur_totale = fields.Float(string="Longueur totale", digits='Product Unit of Measure')
    is_surface         = fields.Float(string="Surface",         digits='Product Unit of Measure', related="product_id.is_surface", readonly=True)
    is_surface_totale  = fields.Float(string="Surface totale",  digits='Product Unit of Measure')
    is_volume          = fields.Float(string="Volume",          digits='Volume', related="product_id.is_volume", readonly=True)
    is_volume_total    = fields.Float(string="Volume total",    digits='Volume')
    is_detail_quantite = fields.Text(string='Détail quantité', compute='_compute_is_detail_quantite')


    @api.depends('product_id', 'product_uom_qty', 'is_longueur_totale', 'is_surface_totale', 'is_volume_total')
    def _compute_is_detail_quantite(self):
        for obj in self:
            x = False
            if obj.product_uom_qty and obj.is_longueur  and obj.is_longueur_totale and obj.is_surface_totale:
                x = "En longueur de %.1fm soit %.1fml ou %.1fm2"%(obj.is_longueur, obj.is_longueur_totale, obj.is_surface_totale)
            obj.is_detail_quantite = x


    @api.depends('product_id', 'product_uom', 'product_uom_qty','is_prix_tarif','is_unite_tarif','product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            price = 0
            if line.product_id:
                for l in line.product_id.product_template_variant_value_ids:
                    if l.attribute_line_id.attribute_id.name=="Longueur":
                        variante = l.product_attribute_value_id.name
                        if variante in ['ml','m2','m','u']:
                            price = line.is_prix_tarif
                if price==0:
                    if line.is_unite_tarif=="m":
                        price = line.is_prix_tarif*line.is_longueur
                    if line.is_unite_tarif=="m2":
                        price = line.is_prix_tarif*line.is_surface
                    if line.is_unite_tarif=="m3":
                        price = line.is_prix_tarif*line.is_volume
                    if line.is_unite_tarif=="unite":
                        price = line.is_prix_tarif
            line.price_unit = price


    @api.onchange('product_id','product_template_id', 'product_uom_qty')
    def _onchange_product_id(self):
        price = 0
        unite = False
        pricelist = self.order_id.pricelist_id
        if pricelist:
            for line in pricelist.item_ids:
                if line.product_id == self.product_id:
                    price = line.fixed_price
                    unite = line.is_unite
                    break
                if line.product_tmpl_id == self.product_template_id and self.product_uom_qty>=line.min_quantity:
                    price = line.fixed_price
                    unite = line.is_unite
                    break
                    
        self.is_prix_tarif  = price
        self.is_unite_tarif = unite



    # @api.onchange('is_prix_tarif','is_unite_tarif','product_uom_qty')
    # def _onchange_is_prix_tarif(self):
    #     price = 0
    #     if self.is_unite_tarif=="m":
    #         price = self.is_prix_tarif*self.is_longueur
    #     if self.is_unite_tarif=="m2":
    #         price = self.is_prix_tarif*self.is_surface
    #     if self.is_unite_tarif=="m3":
    #         price = self.is_prix_tarif*self.is_volume
    #     if self.is_unite_tarif=="unite":
    #         price = self.is_prix_tarif
    #     self.price_unit = price




    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        self.is_longueur_totale = self.product_uom_qty * self.is_longueur
        self.is_surface_totale  = self.product_uom_qty * self.is_surface
        self.is_volume_total    = self.product_uom_qty * self.is_volume


    @api.onchange('is_longueur_totale')
    def _onchange_is_longueur_totale(self):
        qty = surface = volume = 0
        if self.is_longueur>0:
            qty     = self.is_longueur_totale/self.is_longueur
            surface = self.is_longueur_totale * self.product_id.is_largeur/1000
            volume  = self.is_longueur_totale * self.product_id.is_largeur/1000 * self.product_id.is_epaisseur/1000
        self.product_uom_qty   = qty
        self.is_surface_totale = surface
        self.is_volume_total   = volume


    @api.onchange('is_surface_totale')
    def _onchange_is_surface_totale(self):
        qty = 0
        if self.is_surface>0:
            qty = self.is_surface_totale/self.is_surface
        self.product_uom_qty = qty


    @api.onchange('is_volume_total')
    def _onchange_is_volume_total(self):
        qty = 0
        if self.is_volume>0:
            qty = self.is_volume_total/self.is_volume
        self.product_uom_qty = qty


    def _compute_is_composants(self):
        for obj in self:
            t=[]
            for line in obj.is_composants_ids:
                t.append("<div>- %s x %s</div>"%(line.qty, line.composant_id.name))
            html = "\n".join(t)
            obj.is_composants = html

