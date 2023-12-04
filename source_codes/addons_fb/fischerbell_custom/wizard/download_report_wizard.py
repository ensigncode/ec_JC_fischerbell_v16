from odoo import _, api, fields, models

class DownloadReportWizard(models.TransientModel):
    _name = 'download.report.wizard'
    _description = 'Download Report Wizard'

    file = fields.Binary('File')
