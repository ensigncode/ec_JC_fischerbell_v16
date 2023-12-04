# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from markupsafe import Markup

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.safe_eval import safe_eval, time
from odoo.tools.misc import find_in_path
from odoo.tools import check_barcode_encoding, config, is_html_empty, parse_version
from odoo.http import request
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS, FALSE_DOMAIN

import io
import logging
import os
import lxml.html
import tempfile
import subprocess
import re
import json

from lxml import etree
from contextlib import closing
from reportlab.graphics.barcode import createBarcodeDrawing
from PyPDF2 import PdfFileWriter, PdfFileReader, utils
from collections import OrderedDict
from collections.abc import Iterable
from PIL import Image, ImageFile
# Allow truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


_logger = logging.getLogger(__name__)

try:
	createBarcodeDrawing('Code128', value='foo', format='png', width=100, height=100, humanReadable=1).asString('png')
except Exception:
	pass

datamatrix_available = True
try:
	from pylibdmtx import pylibdmtx
except Exception:
	_logger.info('A package may be missing to print Data Matrix barcodes: pylibdmtx or libdmtx.')
	datamatrix_available = False

def _get_wkhtmltopdf_bin():
	return find_in_path('wkhtmltopdf')


# Check the presence of Wkhtmltopdf and return its version at Odoo start-up
wkhtmltopdf_state = 'install'
wkhtmltopdf_dpi_zoom_ratio = False
try:
	process = subprocess.Popen(
		[_get_wkhtmltopdf_bin(), '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)
except (OSError, IOError):
	_logger.info('You need Wkhtmltopdf to print a pdf version of the reports.')
else:
	_logger.info('Will use the Wkhtmltopdf binary at %s' % _get_wkhtmltopdf_bin())
	out, err = process.communicate()
	match = re.search(b'([0-9.]+)', out)
	if match:
		version = match.group(0).decode('ascii')
		if parse_version(version) < parse_version('0.12.0'):
			_logger.info('Upgrade Wkhtmltopdf to (at least) 0.12.0')
			wkhtmltopdf_state = 'upgrade'
		else:
			wkhtmltopdf_state = 'ok'
		if parse_version(version) >= parse_version('0.12.2'):
			wkhtmltopdf_dpi_zoom_ratio = True

		if config['workers'] == 1:
			_logger.info('You need to start Odoo with at least two workers to print a pdf version of the reports.')
			wkhtmltopdf_state = 'workers'
	else:
		_logger.info('Wkhtmltopdf seems to be broken.')
		wkhtmltopdf_state = 'broken'

class IrActionsReport(models.Model):
	_inherit = "ir.actions.report"

	@api.model
	def _run_wkhtmltopdf(
			self,
			bodies,
			report_ref,
			header=None,
			footer=None,
			landscape=False,
			specific_paperformat_args=None,
			set_viewport_size=False):
		'''Execute wkhtmltopdf as a subprocess in order to convert html given in input into a pdf
		document.

		:param list[str] bodies: The html bodies of the report, one per page.
		:param str header: The html header of the report containing all headers.
		:param str footer: The html footer of the report containing all footers.
		:param landscape: Force the pdf to be rendered under a landscape format.
		:param specific_paperformat_args: dict of prioritized paperformat arguments.
		:param set_viewport_size: Enable a viewport sized '1024x1280' or '1280x1024' depending of landscape arg.
		:return: Content of the pdf as bytes
		:rtype: bytes
		'''
		paperformat_id = self.get_paperformat()
		paperformat_id = self._get_report(report_ref).get_paperformat() if report_ref else self.get_paperformat()
		# Build the base command args for wkhtmltopdf bin
		command_args = self._build_wkhtmltopdf_args(
			paperformat_id,
			landscape,
			specific_paperformat_args=specific_paperformat_args,
			set_viewport_size=set_viewport_size)

		files_command_args = []
		temporary_files = []
		if header:
			head_file_fd, head_file_path = tempfile.mkstemp(suffix='.html', prefix='report.header.tmp.')
			with closing(os.fdopen(head_file_fd, 'wb')) as head_file:
				head_file.write(header.encode())
			temporary_files.append(head_file_path)
			files_command_args.extend(['--header-html', head_file_path])
		if footer:
			foot_file_fd, foot_file_path = tempfile.mkstemp(suffix='.html', prefix='report.footer.tmp.')
			with closing(os.fdopen(foot_file_fd, 'wb')) as foot_file:
				foot_file.write(footer.encode())
			temporary_files.append(foot_file_path)
			files_command_args.extend(['--footer-html', foot_file_path])

		paths = []
		for i, body in enumerate(bodies):
			prefix = '%s%d.' % ('report.body.tmp.', i)
			body_file_fd, body_file_path = tempfile.mkstemp(suffix='.html', prefix=prefix)
			with closing(os.fdopen(body_file_fd, 'wb')) as body_file:
				body_file.write(body.encode())
			paths.append(body_file_path)
			temporary_files.append(body_file_path)

		pdf_report_fd, pdf_report_path = tempfile.mkstemp(suffix='.pdf', prefix='report.tmp.')
		os.close(pdf_report_fd)
		temporary_files.append(pdf_report_path)

		try:
			wkhtmltopdf = [_get_wkhtmltopdf_bin()] + command_args + files_command_args + paths + [pdf_report_path]
			process = subprocess.Popen(wkhtmltopdf, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = process.communicate()

			if process.returncode not in [0, 1]:
				if process.returncode == -11:
					message = _(
						'Wkhtmltopdf failed (error code: %s). Memory limit too low or maximum file number of subprocess reached. Message : %s')
				else:
					message = _('Wkhtmltopdf failed (error code: %s). Message: %s')
				_logger.warning(message, process.returncode, err[-1000:])
				raise UserError(message % (str(process.returncode), err[-1000:]))
			else:
				if err:
					_logger.warning('wkhtmltopdf: %s' % err)
		except:
			raise

		with open(pdf_report_path, 'rb') as pdf_document:
			pdf_content = pdf_document.read()

		# Manual cleanup of the temporary files
		for temporary_file in temporary_files:
			try:
				os.unlink(temporary_file)
			except (OSError, IOError):
				_logger.error('Error when trying to remove file %s' % temporary_file)

		return pdf_content


	def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
		if not data:
			data = {}
		data.setdefault('report_type', 'pdf')

		# access the report details with sudo() but evaluation context as current user
		report_sudo = self._get_report(report_ref)

		collected_streams = OrderedDict()

		# Fetch the existing attachments from the database for later use.
		# Reload the stream from the attachment in case of 'attachment_use'.
		if res_ids:
			records = self.env[report_sudo.model].browse(res_ids)
			for record in records:
				stream = None
				attachment = None
				if report_sudo.attachment:
					attachment = report_sudo.retrieve_attachment(record)

					# Extract the stream from the attachment.
					if attachment and report_sudo.attachment_use:
						stream = io.BytesIO(attachment.raw)

						# Ensure the stream can be saved in Image.
						if attachment.mimetype.startswith('image'):
							img = Image.open(stream)
							new_stream = io.BytesIO()
							img.convert("RGB").save(new_stream, format="pdf")
							stream.close()
							stream = new_stream

				collected_streams[record.id] = {
					'stream': stream,
					'attachment': attachment,
				}

		# Call 'wkhtmltopdf' to generate the missing streams.
		res_ids_wo_stream = [res_id for res_id, stream_data in collected_streams.items() if not stream_data['stream']]
		is_whtmltopdf_needed = not res_ids or res_ids_wo_stream

		if is_whtmltopdf_needed:

			if self.get_wkhtmltopdf_state() == 'install':
				# wkhtmltopdf is not installed
				# the call should be catched before (cf /report/check_wkhtmltopdf) but
				# if get_pdf is called manually (email template), the check could be
				# bypassed
				raise UserError(_("Unable to find Wkhtmltopdf on this system. The PDF can not be created."))

			# Disable the debug mode in the PDF rendering in order to not split the assets bundle
			# into separated files to load. This is done because of an issue in wkhtmltopdf
			# failing to load the CSS/Javascript resources in time.
			# Without this, the header/footer of the reports randomly disappear
			# because the resources files are not loaded in time.
			# https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2083
			additional_context = {'debug': False}

			# As the assets are generated during the same transaction as the rendering of the
			# templates calling them, there is a scenario where the assets are unreachable: when
			# you make a request to read the assets while the transaction creating them is not done.
			# Indeed, when you make an asset request, the controller has to read the `ir.attachment`
			# table.
			# This scenario happens when you want to print a PDF report for the first time, as the
			# assets are not in cache and must be generated. To workaround this issue, we manually
			# commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
			if not config['test_enable']:
				additional_context['commit_assetsbundle'] = True

			html = self.with_context(**additional_context)._render_qweb_html(report_ref, res_ids_wo_stream, data=data)[0]

			bodies, html_ids, header, footer, specific_paperformat_args = self._prepare_html(html, report_model=report_sudo.model)

			if report_sudo.attachment and set(res_ids_wo_stream) != set(html_ids):
				raise UserError(_(
					"The report's template %r is wrong, please contact your administrator. \n\n"
					"Can not separate file to save as attachment because the report's template does not contains the"
					" attributes 'data-oe-model' and 'data-oe-id' on the div with 'article' classname.",
					self.name,
				))

			pdf_content = self._run_wkhtmltopdf(
				bodies,
				report_ref=report_ref,
				header=header,
				footer=footer,
				landscape=self._context.get('landscape'),
				specific_paperformat_args=specific_paperformat_args,
				set_viewport_size=self._context.get('set_viewport_size'),
			)
			pdf_content_stream = io.BytesIO(pdf_content)

			# Printing a PDF report without any records. The content could be returned directly.
			if not res_ids:
				return {
					False: {
						'stream': pdf_content_stream,
						'attachment': None,
					}
				}

			# Split the pdf for each record using the PDF outlines.

			# Only one record: append the whole PDF.
			if len(res_ids_wo_stream) == 1:
				collected_streams[res_ids_wo_stream[0]]['stream'] = pdf_content_stream
				return collected_streams

			# In case of multiple docs, we need to split the pdf according the records.
			# To do so, we split the pdf based on top outlines computed by wkhtmltopdf.
			# An outline is a <h?> html tag found on the document. To retrieve this table,
			# we look on the pdf structure using pypdf to compute the outlines_pages from
			# the top level heading in /Outlines.
			html_ids_wo_none = [x for x in html_ids if x]
			if len(res_ids_wo_stream) > 1 and set(res_ids_wo_stream) == set(html_ids_wo_none):
				reader = PdfFileReader(pdf_content_stream)
				root = reader.trailer['/Root']
				has_valid_outlines = '/Outlines' in root and '/First' in root['/Outlines']
				if not has_valid_outlines:
					return {False: {
						'report_action': self,
						'stream': pdf_content_stream,
						'attachment': None,
					}}

				outlines_pages = []
				node = root['/Outlines']['/First']
				while True:
					outlines_pages.append(root['/Dests'][node['/Dest']][0])
					if '/Next' not in node:
						break
					node = node['/Next']
				outlines_pages = sorted(set(outlines_pages))

				# The number of outlines must be equal to the number of records to be able to split the document.
				has_same_number_of_outlines = len(outlines_pages) == len(res_ids)

				# There should be a top-level heading on first page
				has_top_level_heading = outlines_pages[0] == 0

				if has_same_number_of_outlines and has_top_level_heading:
					# Split the PDF according to outlines.
					for i, num in enumerate(outlines_pages):
						to = outlines_pages[i + 1] if i + 1 < len(outlines_pages) else reader.numPages
						attachment_writer = PdfFileWriter()
						for j in range(num, to):
							attachment_writer.addPage(reader.getPage(j))
						stream = io.BytesIO()
						attachment_writer.write(stream)
						collected_streams[res_ids[i]]['stream'] = stream

					return collected_streams

			collected_streams[False] = {'stream': pdf_content_stream}

		return collected_streams