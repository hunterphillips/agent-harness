# ServiceNow Scripting Best Practices

> Concise reference for writing correct, performant ServiceNow server-side and client-side scripts in a Fluent SDK project.

## Server-Side Scripts (`.server.js`)

### Variable Naming

Avoid generic names like `gr`. Use descriptive names that include the table or purpose — especially for `GlideRecord` variables, since multiple queries in the same scope are common and collisions cause hard-to-trace bugs.

```javascript
// Bad
var gr = new GlideRecord('incident');

// Good
var grIncident = new GlideRecord('incident');
var grAssignmentGroup = new GlideRecord('sys_user_group');
```

### GlideRecord Patterns

**Use `addEncodedQuery()` for complex queries** instead of chaining `addQuery()` / `addOrCondition()`. Easier to maintain and matches the filter syntax visible in the platform UI.

```javascript
// Good
var query = 'active=true^priority=1^ORpriority=2';
var grIncident = new GlideRecord('incident');
grIncident.addEncodedQuery(query);
grIncident.query();
```

**Use `GlideAggregate` for counting**, never `getRowCount()`. `getRowCount()` loads every matching record into memory.

```javascript
// Good
var aggIncident = new GlideAggregate('incident');
aggIncident.addAggregate('COUNT');
aggIncident.addQuery('active', true);
aggIncident.query();
if (aggIncident.next()) var count = aggIncident.getAggregate('COUNT');

// Bad — loads all records just to count them
var grIncident = new GlideRecord('incident');
grIncident.addQuery('active', true);
grIncident.query();
var count = grIncident.getRowCount();
```

**Use `setLimit()` for existence checks.** If you only need to know whether a record exists, don't retrieve every match.

```javascript
var grIncident = new GlideRecord('incident');
grIncident.addQuery('active', true);
grIncident.setLimit(1);
grIncident.query();
if (grIncident.hasNext()) {
  /* at least one exists */
}
```

**Never dot-walk to `.sys_id` on a reference field.** The value of a reference field _is_ the sys_id. Dot-walking triggers an unnecessary extra query.

```javascript
// Bad — extra database lookup
var id = current.caller_id.sys_id;

// Good
var id = current.getValue('caller_id');
```

**Use `getDisplayValue()`** instead of hard-coding the display column name (e.g., `.name`, `.number`). Survives dictionary changes.

```javascript
var parentDisplay = current.parent.getDisplayValue();
```

### Business Rules

| When value | Use for                                                                         |
| ---------- | ------------------------------------------------------------------------------- |
| `display`  | Pushing data to client via `g_scratchpad`                                       |
| `before`   | Modifying fields on the _current_ record (auto-saved, no `update()` needed)     |
| `after`    | Updating _related_ records that must appear immediately                         |
| `async`    | Updating related records that don't need to display immediately (metrics, SLAs) |

**Never call `current.update()` in a Business Rule.** It can trigger recursive execution. Changes in `before` rules are auto-saved. For the rare exception, pair with `current.setWorkflow(false)` to suppress re-triggering.

**Prefer to set a condition.** Business Rules without a condition fire on every insert/update/delete, wasting cycles. Use the `filter_condition` field.

### General Server Script Hygiene

- **Avoid hard-coded sys_ids or names.** Use `gs.getProperty()` or look up by reference. Sys_ids differ between instances; names change with org restructuring.
- **Verify values before use.** Dot-walking through an empty reference field returns undefined and pollutes logs.

```javascript
// Good
var userId = gs.getUserID();
var isOwner = userId == current.assigned_to;
var isCaller = userId == current.caller_id;
```

## Client-Side Scripts (`.client.js`)

### Performance Hierarchy

1. **Use data already on the form** (`g_form.getValue()`) — instant, no cost.
2. **Use `g_scratchpad`** — populated once on form load via a `display` Business Rule. Zero additional round-trips.
3. **Use asynchronous `GlideAjax`** — for dynamic server lookups. Prefer `getXML()` (async) over `getXMLWait()` (sync/blocking).
4. **Avoid `GlideRecord` and `getReference()`** on the client — they fetch all fields and are synchronous. Not available in scoped apps.

### onChange Best Practices

Layer these guards top-to-bottom to avoid unnecessary work:

```javascript
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
  if (isLoading) return; // 1. Skip on initial form load
  if (!newValue) return; // 2. Skip if field was cleared
  if (newValue == oldValue) return; // 3. Skip if value didn't actually change

  // 4. Check client-side conditions before making server calls
  if (g_form.getValue('assignment_group') == '') {
    var gaSupport = new GlideAjax('MyAjaxUtil');
    gaSupport.addParam('sysparm_name', 'getAnswer');
    gaSupport.addParam('sysparm_input', newValue);
    gaSupport.getXML(function (response) {
      var answer = response.responseXML.documentElement.getAttribute('answer');
      g_form.setValue('target_field', answer);
    });
  }
}
```

### Things to Avoid

- **Global Client Scripts** (table = "Global") — load on every form in the system. Attach to a base table like `task` instead so child tables inherit.
- **DOM manipulation** — fragile across platform upgrades. Use `g_form` API. Exception: UI Pages and Service Portal widgets where you own the DOM.
- **UI Policies for field attributes** — prefer UI Policies (no-code) over Client Scripts for setting mandatory/read-only/visible.

## Debugging Conventions

Use property-controlled `gs.debug()` so debug output can be toggled without code changes:

```javascript
initialize: function() {
    this.debug = gs.getProperty('debug.MyUtil') == 'true';
},
_debug: function(msg) {
    if (this.debug) gs.debug('>>>DEBUG: MyUtil: ' + msg);
},
```
