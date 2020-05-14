from collections import OrderedDict
from operator import itemgetter

from odoo import http, _
from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
    pager as portal_pager,
)
from odoo.http import request
from odoo.tools import groupby as groupbyelem


class ProjectPortal(CustomerPortal):

    @http.route()
    def portal_my_tasks(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in="content",
        groupby="project",
        **kw
    ):
        res_values = super().portal_my_tasks(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            **kw
        )
        task_count = res_values.qcontext.get("task_count", 0)
        pager = portal_pager(
            url="/my/tasks",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "search_in": search_in,
                "search": search,
                "groupby": groupby,
            },
            total=task_count,
            page=page,
            step=self._items_per_page,
        )
        res_values.qcontext.update({"pager": pager})
        if res_values.qcontext.get("searchbar_groupby", False):
            searchbar_groupby = OrderedDict()
            for dict_key in sorted(res_values.qcontext["searchbar_groupby"]):
                searchbar_groupby.update(
                    {
                        dict_key: res_values.qcontext["searchbar_groupby"][
                            dict_key
                        ]
                    }
                )
            searchbar_groupby.update(
                {"stage": {"input": "stage", "label": _("Stage")}}
            )
            res_values.qcontext.update(
                {"searchbar_groupby": searchbar_groupby}
            )
        if groupby == "stage":
            tasks = res_values.qcontext["grouped_tasks"][0]
            grouped_tasks = [
                request.env["project.task"].concat(*g)
                for k, g in groupbyelem(tasks, itemgetter("stage_id"))
            ]
            res_values.qcontext.update({"grouped_tasks": grouped_tasks})
            res_values.qcontext.update({"groupby": "stage"})
        return res_values
