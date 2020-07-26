=======================================================
Force to set a timesheets Billable Type to Non Billable
=======================================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fsale_timesheet_force_non_billable-lightgray.png?logo=github
    :target: https://github.com/druidoo/druidoo-addons/tree/12.0


|badge1| |badge2| |badge3|

    This module helps you to set a timesheet to **Non Billable** forcefully.


**Table of contents**


.. contents::
   :local:


Usage
=====

* In a **Timesheets** tab of a task, you will find 2 buttons in Timesheet lines(Any of the buttons will be visible at a time).

* Using these 2 buttons you can set/remove the **Billable Type** of a timesheet to **Non Billable** forcefully.

* If you **set** the timesheet to forcefully consider the timesheet as Non Billable, then it **will not look** for the sale order line or any product configuration to set Billable Type

* If you **unset** the timesheet to forcefully consider the timesheet as Non Billable, then it **will look** for the sale order line and SO line product's configuration to set Billable Type

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/druidoo/FoodCoops/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/druidoo/FoodCoops/issues/new?body=module:%20purchase_compute_order%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Druidoo


Contributors
~~~~~~~~~~~~

* Druidoo <https://www.druidoo.io>
