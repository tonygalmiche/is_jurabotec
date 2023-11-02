# -*- coding: utf-8 -*-
from odoo import models,fields,api
import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
import unicodedata
import base64


def s(txt,lg):
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode()
    txt = (txt+'                                                             ')[:lg]
    return txt


class is_export_compta(models.Model):
    _name='is.export.compta'
    _description='is.export.compta'
    _order='name desc'

    name               = fields.Char("N°Folio"      , readonly=True)
    type_interface     = fields.Selection([('ventes', 'Ventes'),('achats', 'Achats')], "Interface", required=True, default="ventes")
    date_fin           = fields.Date("Date de fin", default=fields.Date.today, required=True)
    ligne_ids          = fields.One2many('is.export.compta.ligne', 'export_compta_id', 'Lignes')
    file_ids           = fields.Many2many('ir.attachment', 'is_export_compta_attachment_rel', 'export_id', 'attachment_id', 'Pièces jointes')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta')
        res = super(is_export_compta, self).create(vals)
        return res


    def action_export_compta(self):
        cr=self._cr
        for obj in self:
            invoices = self.env['account.move'].search([('is_export_compta_id','=',obj.id)])
            for invoice in invoices:
                invoice.is_export_compta_id=False
            obj.ligne_ids.unlink()
            if obj.type_interface=='ventes':
                type_facture=['out_invoice', 'out_refund']
                journal='VE'
            else:
                type_facture=['in_invoice', 'in_refund']
                journal='AC'
            filter=[
                ('state'    , 'in' , ['posted']),
                ('move_type', 'in' , type_facture),
                ('invoice_date', '<=', obj.date_fin),
                ('is_export_compta_id', '=', False),
            ]



            invoices = self.env['account.move'].search(filter, order="invoice_date,id")
            if len(invoices)==0:
                raise ValidationError('Aucune facture à traiter')
            for invoice in invoices:
                sql="""
                    SELECT  
                        ai.invoice_date,
                        aa.code, 
                        ai.name piece, 
                        rp.name libelle, 
                        ai.move_type, 
                        rp.is_code_comptable_client,
                        sum(aml.debit) debit, 
                        sum(aml.credit) credit,
                        rp.id partner_id,
                        ai.id
                    FROM account_move_line aml inner join account_move ai      on aml.move_id=ai.id
                                               inner join account_account aa   on aml.account_id=aa.id
                                               inner join res_partner rp       on ai.partner_id=rp.id
                    WHERE ai.id=%s
                    GROUP BY ai.invoice_date, ai.id, ai.name, rp.id, rp.name, aa.code, ai.move_type, rp.is_code_comptable_client, ai.invoice_date_due
                    ORDER BY ai.invoice_date, ai.id, ai.name, rp.id, rp.name, aa.code, ai.move_type, rp.is_code_comptable_client, ai.invoice_date_due
                """
                cr.execute(sql,[invoice.id])
                for row in cr.dictfetchall():
                    invoice.is_export_compta_id = obj.id
                    compte=str(row["code"])
                    if obj.type_interface=='ventes' and compte=='411100':
                        compte=str(row["is_code_comptable_client"])
                    vals={
                        'export_compta_id'  : obj.id,
                        'date_facture'      : row["invoice_date"],
                        'journal'           : journal,
                        'compte'            : compte,
                        'libelle'           : row["libelle"],
                        'debit'             : row["debit"],
                        'credit'            : row["credit"],
                        'devise'            : 'E',
                        'piece'             : row["piece"],
                        'commentaire'       : False,
                        'partner_id'        : row["partner_id"],
                        'invoice_id'        : invoice.id,

                    }
                    self.env['is.export.compta.ligne'].create(vals)
            self.generer_fichier_cegid()


    def generer_fichier_cegid(self):
        for obj in self:
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id)])
            attachments.unlink()
            name='export-compta.txt'
            dest     = '/tmp/'+name
            f = open(dest,'w')
            for row in obj.ligne_ids:
                compte=str(row.compte)
                if compte=='None':
                    compte=''
                debit=row.debit
                credit=row.credit
                montant=credit-debit
                if montant>0.0:
                    sens='C'
                else:
                    montant=-montant
                    sens='D'
                montant=('000000000000'+str(int(round(100*montant))))[-12:]
                date_facture=row.date_facture
                date_facture=date_facture.strftime('%d%m%y')
                libelle=s(row.libelle,20)
                piece=(row.piece[-8:]+u'        ')[0:8]
                f.write('M')
                f.write((compte+'00000000')[0:8])
                f.write(row.journal)
                f.write('000')
                f.write(date_facture)
                f.write('F')
                f.write(libelle)
                f.write(sens)
                f.write('+')
                f.write(montant)
                f.write('        ')
                f.write('000000')
                f.write('     ')
                f.write(piece)
                f.write('                 ')
                f.write(piece)
                f.write('EURVE    ')
                f.write(libelle)
                f.write('\r\n')
            f.close()
            r = open(dest,'rb').read()
            r = base64.b64encode(r)
            vals = {
                'name':        name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            attachment = self.env['ir.attachment'].create(vals)
            obj.file_ids=[(6,0,[attachment.id])]


class is_export_compta_ligne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = u"Lignes d'export en compta"
    _order='date_facture'

    export_compta_id = fields.Many2one('is.export.compta', 'Export Compta', required=True, ondelete='cascade')
    date_facture     = fields.Date("Date")
    journal          = fields.Char("Journal", default='VTE')
    compte           = fields.Char("N°Compte")
    piece            = fields.Char("Pièce")
    libelle          = fields.Char("Libellé")
    debit            = fields.Float("Débit")
    credit           = fields.Float("Crédit")
    devise           = fields.Char("Devise", default='E')
    commentaire      = fields.Char("Commentaire")
    partner_id       = fields.Many2one('res.partner', 'Partenaire')
    invoice_id       = fields.Many2one('account.move', 'Facture')
