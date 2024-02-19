====================
 Using the profiler
====================

The profiler allows to profile specific functions of your code.  This document
demonstrate its usage in a specific case.


Determining performance issues when validating invoices
=======================================================

Validating invoices in Odoo may take several minutes.  Specially when the
invoices have analytic accounts in many lines (we require all lines to have
analytic accounts).

Previously, by manually running all the steps in the 'invoice_open' signal of
the workflow, we have determined that the function that takes the longest is
the `action_move_create`:func:

So we modify the ``account_invoice.py`` module like this::

  $ git diff -- addons/account/account_invoice.py
  diff --git a/addons/account/account_invoice.py b/addons/account/account_invoice.py
  index e8870e8e697..1072835f982 100644
  --- a/addons/account/account_invoice.py
  +++ b/addons/account/account_invoice.py
  @@ -28,6 +28,9 @@ from openerp.exceptions import except_orm, Warning, RedirectWarning
   from openerp.tools import float_compare
   import openerp.addons.decimal_precision as dp

  +from xoeuf.tools.profiler import profile
  +
  +
   # mapping invoice type to journal type
   TYPE2JOURNAL = {
       'out_invoice': 'sale',
  @@ -796,6 +799,7 @@ class account_invoice(models.Model):
                   line.append((0,0,val))
           return line

  +    @profile
       @api.multi
       def action_move_create(self):
           """ Creates invoice related analytics and financial move lines """


Now we open a shell::

  $ bin/xoeuf shell -d db1

and type::

  >>> from xoeuf.models.proxy import AccountInvoice as Invoice

  >>> # Select invoices with at least 4 items.  You should make sure they all
  ... # have analytic accounts
  >>> invoices = Invoice.search([('state', '=', 'draft')]).filtered(
  ...               lambda i: len(i.invoice_line) > 3)
  >>> inv = invoices[0]

  >>> inv.signal_workflow('invoice_open')

We wait for a while here and we get the following (I'm omitting many lines
since you may get the idea from this)::

  Timer unit: 1e-06 s

  Total time: 80.3346 s
  File: /home/manu/src/merchise/pgi/odoo/addons/account/account_invoice.py
  Function: action_move_create at line 802

  Line #      Hits         Time  Per Hit   % Time  Line Contents
  ==============================================================
     802                                               @profile
     803                                               @api.multi
     804                                               def action_move_create(self):
     805                                                   """ Creates invoice related analytics and financial move lines """
     806         1           15     15.0      0.0          account_invoice_tax = self.env['account.invoice.tax']
     807         1            6      6.0      0.0          account_move = self.env['account.move']
     808
     809         2           11      5.5      0.0          for inv in self:

         omitted lines

     941         1            1      1.0      0.0              ctx['invoice'] = inv
     942         1            2      2.0      0.0              ctx_nolang = ctx.copy()
     943         1            2      2.0      0.0              ctx_nolang.pop('lang', None)
     944         1     42188841 42188841.0     52.5              move = account_move.with_context(ctx_nolang).create(move_vals)
     945
     946                                                       # make the invoice point to that move
     947         1            3      3.0      0.0              vals = {
     948         1            4      4.0      0.0                  'move_id': move.id,
     949         1            5      5.0      0.0                  'period_id': period.id,
     950         1         1196   1196.0      0.0                  'move_name': move.name,
     951                                                       }
     952         1        75528  75528.0      0.1              inv.with_context(ctx).write(vals)
     953                                                       # Pass invoice in context in method post: used if you want to get the same
     954                                                       # account move reference when creating the same invoice after a cancelled one:
     955         1     37697598 37697598.0     46.9              move.post()
     956         1            7      7.0      0.0          self._log_event()
     957         1            1      1.0      0.0          return True


The column of interest is the '% Time'.  We clearly see that there two calls
that take each about the 50% of the time.  Now we ``@profile`` both the
`create` and `post` methods::

  $ git diff -- addons/account
  diff --git a/addons/account/account.py b/addons/account/account.py
  index 4f37edac0f1..3b735b4b0a6 100644
  --- a/addons/account/account.py
  +++ b/addons/account/account.py
  @@ -35,8 +35,11 @@ from openerp.tools.safe_eval import safe_eval as eval

   import openerp.addons.decimal_precision as dp

  +from xoeuf.tools.profiler import profile
  +
   _logger = logging.getLogger(__name__)

  +
   def check_cycle(self, cr, uid, ids, context=None):
       """ climbs the ``self._table.parent_id`` chains for 100 levels or
       until it can't find any more parent(s)
  @@ -1318,6 +1321,7 @@ class account_move(osv.osv):
               ['journal_id']),
       ]

  +    @profile
       def post(self, cr, uid, ids, context=None):
           if context is None:
               context = {}
  @@ -1389,6 +1393,7 @@ class account_move(osv.osv):
           self.validate(cr, uid, ids, context=context)
           return result

  +    @profile
       def create(self, cr, uid, vals, context=None):
           context = dict(context or {})
           if vals.get('line_id'):


And now, let's go back to our shell::

  $ bin/xoeuf shell -d db1

  >>> from xoeuf.models.proxy import AccountInvoice as Invoice

  >>> # Select invoices with at least 4 items.  You should make sure they all
  ... # have analytic accounts
  >>> invoices = Invoice.search([('state', '=', 'draft')]).filtered(
  ...               lambda i: len(i.invoice_line) > 3)
  >>> inv = invoices[0]

  >>> inv.signal_workflow('invoice_open')


The result this time is like::

  Timer unit: 1e-06 s

  Total time: 268.336 s
  File: /home/manu/src/merchise/pgi/odoo/addons/account/account.py
  Function: create at line 1396

  Line #      Hits         Time  Per Hit   % Time  Line Contents
  ==============================================================
    1396                                               @profile
    1397                                               def create(self, cr, uid, vals, context=None):
    1398         1            3      3.0      0.0          context = dict(context or {})
    1399         1            1      1.0      0.0          if vals.get('line_id'):

               omitted

    1420         1            1      1.0      0.0              c['journal_id'] = vals['journal_id']
    1421         1            1      1.0      0.0              if 'date' in vals: c['date'] = vals['date']
    1422         1      9166265 9166265.0      3.4              result = super(account_move, self).create(cr, uid, vals, c)
    1423         1    259169623 259169623.0     96.6              tmp = self.validate(cr, uid, [result], context)
    1424         1           40     40.0      0.0              journal = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'], context)
    1425         1           18     18.0      0.0              if journal.entry_posted and tmp:
    1426                                                           self.button_validate(cr,uid, [result], context)
    1427                                                   else:
    1428                                                       result = super(account_move, self).create(cr, uid, vals, context)
    1429         1            0      0.0      0.0          return result


  Timer unit: 1e-06 s

  Total time: 551.155 s
  File: /home/manu/src/merchise/pgi/odoo/addons/account/account.py
  Function: post at line 1324

  Line #      Hits         Time  Per Hit   % Time  Line Contents
  ==============================================================
    1324                                               @profile
    1325                                               def post(self, cr, uid, ids, context=None):
    1326         1            1      1.0      0.0          if context is None:
    1327                                                       context = {}
    1328         1            1      1.0      0.0          invoice = context.get('invoice', False)
    1329         1    265463635 265463635.0     48.2          valid_moves = self.validate(cr, uid, ids, context)
    1330
    1331         1            1      1.0      0.0          if not valid_moves:

         omitted

    1348         1            2      2.0      0.0                  if new_name:
    1349         1    285492299 285492299.0     51.8                      self.write(cr, uid, [move.id], {'name':new_name})
    1350
    1351         1            1      1.0      0.0          cr.execute('UPDATE account_move '\
    1352                                                              'SET state=%s '\
    1353                                                              'WHERE id IN %s',
    1354         1          395    395.0      0.0                     ('posted', tuple(valid_moves),))
    1355         1           79     79.0      0.0          self.invalidate_cache(cr, uid, ['state', ], valid_moves, context=context)
    1356         1            1      1.0      0.0          return True


Now we notice that `validate` is called two time in these methods, that one
more time in the `write` (which takes the other big piece of the pie).

When profiling validate we notice that it passes most of the time creating
analytic line (you'd say that creating analytic lines must not be part of the
validate function, would you?)::

  Timer unit: 1e-06 s

  Total time: 297.801 s
  File: /home/manu/src/merchise/pgi/odoo/addons/account/account.py
  Function: validate at line 1550

  Line #      Hits         Time  Per Hit   % Time  Line Contents
  ==============================================================
    1550                                               @profile
    1551                                               def validate(self, cr, uid, ids, context=None):
    1552         1            3      3.0      0.0          if context and ('__last_update' in context):
    1553                                                       del context['__last_update']
    1554
    1555         1            1      1.0      0.0          valid_moves = [] #Maintains a list of moves which can be responsible to create analytic entries
    1556         1            7      7.0      0.0          obj_analytic_line = self.pool.get('account.analytic.line')
    1557         1            2      2.0      0.0          obj_move_line = self.pool.get('account.move.line')
    1558         1            2      2.0      0.0          obj_precision = self.pool.get('decimal.precision')
    1559         1           62     62.0      0.0          prec = obj_precision.precision_get(cr, uid, 'Account')
    1560         2          111     55.5      0.0          for move in self.browse(cr, uid, ids, context):
    1561         1         2115   2115.0      0.0              journal = move.journal_id
    1562         1            1      1.0      0.0              amount = 0
    1563         1            1      1.0      0.0              line_ids = []
    1564         1            1      1.0      0.0              line_draft_ids = []
    1565         1            2      2.0      0.0              company_id = None
    1566                                                       # makes sure we don't use outdated period
    1567         1          626    626.0      0.0              obj_move_line._update_journal_check(cr, uid, journal.id, move.period_id.id, context=context)
    1568        32         6393    199.8      0.0              for line in move.line_id:
    1569        31        32036   1033.4      0.0                  amount += line.debit - line.credit
    1570        31           98      3.2      0.0                  line_ids.append(line.id)
    1571        31          213      6.9      0.0                  if line.state=='draft':
    1572        31           92      3.0      0.0                      line_draft_ids.append(line.id)
    1573
    1574        31           26      0.8      0.0                  if not company_id:
    1575         1         1979   1979.0      0.0                      company_id = line.account_id.company_id.id
    1576        31          536     17.3      0.0                  if not company_id == line.account_id.company_id.id:
    1577                                                               raise osv.except_osv(_('Error!'), _("Cannot create moves for different companies."))
    1578
    1579        31          392     12.6      0.0                  if line.account_id.currency_id and line.currency_id:
    1580                                                               if line.account_id.currency_id.id != line.currency_id.id and (line.account_id.currency_id.id != line.account_id.company_id.currency_id.id):
    1581                                                                   raise osv.except_osv(_('Error!'), _("""Cannot create move with currency different from ..""") % (line.account_id.code, line.account_id.name))
    1582
    1583         1           18     18.0      0.0              if round(abs(amount), prec) < 10 ** (-max(5, prec)):
    1584                                                           # If the move is balanced
    1585                                                           # Add to the list of valid moves
    1586                                                           # (analytic lines will be created later for valid moves)
    1587         1            2      2.0      0.0                  valid_moves.append(move)
    1588
    1589                                                           # Check whether the move lines are confirmed
    1590
    1591         1            1      1.0      0.0                  if not line_draft_ids:
    1592                                                               continue
    1593                                                           # Update the move lines (set them as valid)
    1594
    1595         1            3      3.0      0.0                  obj_move_line.write(cr, uid, line_draft_ids, {
    1596         1            1      1.0      0.0                      'state': 'valid'
    1597         1        65123  65123.0      0.0                  }, context=context, check=False)
    1598

    BY THE WAY, from 1599 to 1617 does NOTHING BUT TO WASTE TIME

    1599         1            2      2.0      0.0                  account = {}
    1600         1            1      1.0      0.0                  account2 = {}
    1601
    1602         1           23     23.0      0.0                  if journal.type in ('purchase','sale'):
    1603        32          114      3.6      0.0                      for line in move.line_id:
    1604        31           27      0.9      0.0                          code = amount = 0
    1605        31          561     18.1      0.0                          key = (line.account_id.id, line.tax_code_id.id)
    1606        31           29      0.9      0.0                          if key in account2:
    1607                                                                       code = account2[key][0]
    1608                                                                       amount = account2[key][1] * (line.debit + line.credit)
    1609        31          254      8.2      0.0                          elif line.account_id.id in account:
    1610                                                                       code = account[line.account_id.id][0]
    1611                                                                       amount = account[line.account_id.id][1] * (line.debit + line.credit)
    1612        31           31      1.0      0.0                          if (code or amount) and not (line.tax_code_id or line.tax_amount):
    1613                                                                       obj_move_line.write(cr, uid, [line.id], {
    1614                                                                           'tax_code_id': code,
    1615                                                                           'tax_amount': amount
    1616                                                                       }, context=context, check=False)
    1617                                                       elif journal.centralisation:
    1618                                                           # If the move is not balanced, it must be centralised...
    1619
    1620                                                           # Add to the list of valid moves
    1621                                                           # (analytic lines will be created later for valid moves)
    1622                                                           valid_moves.append(move)
    1623
    1624                                                           #
    1625                                                           # Update the move lines (set them as valid)
    1626                                                           #
    1627                                                           self._centralise(cr, uid, move, 'debit', context=context)
    1628                                                           self._centralise(cr, uid, move, 'credit', context=context)
    1629                                                           obj_move_line.write(cr, uid, line_draft_ids, {
    1630                                                               'state': 'valid'
    1631                                                           }, context=context, check=False)
    1632                                                       else:
    1633                                                           # We can't validate it (it's unbalanced)
    1634                                                           # Setting the lines as draft
    1635                                                           not_draft_line_ids = list(set(line_ids) - set(line_draft_ids))
    1636                                                           if not_draft_line_ids:
    1637                                                               obj_move_line.write(cr, uid, not_draft_line_ids, {
    1638                                                                   'state': 'draft'
    1639                                                               }, context=context, check=False)
    1640                                                   # Create analytic lines for the valid moves
    1641         2            4      2.0      0.0          for record in valid_moves:
    1642        32    297689833 9302807.3    100.0              obj_move_line.create_analytic_lines(cr, uid, [line.id for line in record.line_id], context)
    1643
    1644         2           10      5.0      0.0          valid_moves = [move.id for move in valid_moves]
    1645         1            1      1.0      0.0          return len(valid_moves) > 0 and valid_moves or False


So the plan is to avoid calling ``validate``, or to extract the
``create_analytic_lines`` to other part of the code.
