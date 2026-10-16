"""Writing events into an interaction.

Demonstrates : `ModuleExecutor`, and the difference between the four ways a
               module can leave something behind: a chat message, a context
               variable, a store value, and a diagnostic *event*. Also a
               `ListAttribute` whose select allows each option once
               (`unique_in_list`).
Documented in: docs/06-events-in-interactions.md
Change first : the `debug_type` and the messages in `execute()`.

The key idea: anything you pass to `add_debug_info()` ends up in
`ModuleResponses.debug`, and the platform turns each entry into a row in its
`discussion_events` table with `type = 'proxy_module'`. Those rows are what
you see in the **Events** panel when you open an interaction in the admin UI,
and what `GET /api/discussions/{id}/events` returns. That is the fastest way
to prove your addon actually ran.
"""

from typing import override

from cw_addons.modules.executor import ModuleExecutor
from cw_addons.modules.models import (
    DebugInfoType,
    LangString,
    ListAttribute,
    ModuleResponses,
    OutputContext,
    OutputPortStatic,
    SelectAttribute,
    StringAttribute,
)
from cw_addons.modules.module import Module
from pydantic import BaseModel


class ContextValue(BaseModel):
    key: str | None = None
    value: str | None = None


class InteractionEventAttributes(BaseModel):
    event_message: str
    severity: str
    context_values: list[ContextValue] = []


class InteractionEventModule(Module[InteractionEventAttributes]):
    attributes: InteractionEventAttributes

    name = "interaction_event"
    version = "v2"
    public = True

    icon = "📝"
    category = LangString(en="Examples", cs="Příklady")
    title = LangString(en="Write Interaction Event", cs="Zápis události do interakce")
    short_description = LangString(
        en="Writes a diagnostic event into the interaction.",
        cs="Zapíše diagnostickou událost do interakce.",
    )
    description = LangString(
        en=(
            "Writes one event into the interaction's Events panel, and also sets a context "
            "variable and a store value so you can compare the three mechanisms side by side."
        ),
        cs=(
            "Zapíše jednu událost do panelu Události v interakci a zároveň nastaví kontextovou "
            "proměnnou a hodnotu ve store, abyste viděli rozdíl mezi těmito mechanismy."
        ),
    )

    input_attributes = [
        StringAttribute(
            name="event_message",
            title=LangString(en="Event message", cs="Text události"),
            description=LangString(
                en="Text written into the interaction's event log.",
                cs="Text zapsaný do logu událostí interakce.",
            ),
            default_value="Example addon reached this node",
            required=True,
        ),
        SelectAttribute(
            name="severity",
            title=LangString(en="Severity", cs="Závažnost"),
            description=LangString(
                en="Maps directly to the severity column of the stored event.",
                cs="Odpovídá sloupci severity u uložené události.",
            ),
            # SelectAttribute options are single-entry {value: label} maps.
            options=[{"info": "Info"}, {"warning": "Warning"}, {"error": "Error"}],
            default_value="info",
            required=True,
        ),
        ListAttribute(
            name="context_values",
            title=LangString(en="Context values", cs="Kontextové hodnoty"),
            description=LangString(
                en="Extra context variables to set, one per row.",
                cs="Další kontextové proměnné k nastavení, jedna na řádek.",
            ),
            attributes=[
                SelectAttribute(
                    name="key",
                    title=LangString(en="Variable", cs="Proměnná"),
                    description=LangString(en="Which variable to set.", cs="Kterou proměnnou nastavit."),
                    options=[{"order_id": "Order ID"}, {"customer_id": "Customer ID"}],
                    # Each variable can be picked in one row only: the builder hides
                    # the ones other rows already use.
                    unique_in_list=True,
                ),
                StringAttribute(name="value", title=LangString(en="Value", cs="Hodnota")),
            ],
        ),
    ]

    output_contexts = [
        OutputContext(
            name="last_event_message",
            title=LangString(en="Last event message", cs="Poslední text události"),
            description=LangString(
                en="Readable by later nodes in the flow as a context variable.",
                cs="Dostupné dalším uzlům toku jako kontextová proměnná.",
            ),
        ),
    ]

    output_ports = [
        OutputPortStatic(
            name="done",
            title=LangString(en="Done", cs="Hotovo"),
            description=LangString(en="Always taken.", cs="Vždy."),
        ),
    ]

    @override
    async def execute(self) -> ModuleResponses:
        executor = ModuleExecutor(
            discussion=self.discussion,
            attributes=self.attributes,
            tenant=self.tenant,
            module_name=self.name,
        )

        # 1. A diagnostic EVENT. Not visible to the customer. Lands in the
        #    interaction's Events panel and in discussion_events.
        executor.add_debug_info(
            message=self.attributes.event_message,
            debug_type=DebugInfoType(self.attributes.severity),
        )

        # 2. A CONTEXT variable. Business data for later nodes in this flow.
        executor.add_context("last_event_message", self.attributes.event_message)
        # unique_in_list is only a builder rule, so a flow saved before it can
        # still repeat a key; the later row wins, as it would for the designer.
        for row in self.attributes.context_values:
            if row.key and row.value:
                executor.add_context(row.key, row.value)

        # 3. A STORE value. Like context, but it survives across the whole
        #    conversation rather than being recomputed per flow run.
        executor.add_store({"example_addon_last_run": self.discussion.sequence})

        # 4. A chat MESSAGE. The only one of the four the customer ever sees.
        executor.add_message(f"Event written: {self.attributes.event_message}")

        # Which arrow out of this node the flow follows.
        executor.add_output_port("done")

        # `get_response()` bundles the actions, the debug entries and the
        # next sequence number into the response the platform expects.
        return executor.get_response()
