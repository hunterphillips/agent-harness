---
name: servicenow-fluent
description: Use when writing or modifying ServiceNow Fluent code, .now.ts files, or any @servicenow/sdk import. Use when creating or editing Records, SPWidgets, ACLs, BusinessRules, ClientScripts, ScriptIncludes, Tables, ScriptedRestApis, UIActions, or any ServiceNow application artifact. Use when unsure about Fluent API shape, parameters, or patterns.
---

# ServiceNow Fluent API Reference

## Overview

Local SDK examples are cloned at `sdk-reference/`. Read specific files when you need API patterns or parameter shapes.

## Quick Reference

| API | Import | Example Path |
|---|---|---|
| `Record` | `@servicenow/sdk/core` | `sdk-reference/record-sample/src/fluent/record-incident.now.ts` |
| `SPWidget` | `@servicenow/sdk/core` | `sdk-reference/service-portal-sample/src/fluent/widgets/sample-widget.now.ts` |
| `Acl` / `Role` | `@servicenow/sdk/core` | `sdk-reference/acl-sample/src/fluent/index.now.ts` |
| `BusinessRule` | `@servicenow/sdk/core` | `sdk-reference/businessrule-sample/src/fluent/business-rule-1.now.ts` |
| `ClientScript` | `@servicenow/sdk/core` | `sdk-reference/clientscript-sample/src/fluent/clientscript.now.ts` |
| `ScriptInclude` | `@servicenow/sdk/core` | `sdk-reference/script-include-sample/src/fluent/MyScriptInclude.now.ts` |
| `Table` | `@servicenow/sdk/core` | `sdk-reference/table-sample/` |
| `ScriptedRestApi` | `@servicenow/sdk/core` | `sdk-reference/restapi-sample/src/fluent/rest-api-simple.now.ts` |
| `ScriptAction` | `@servicenow/sdk/core` | `sdk-reference/scriptaction-sample/src/fluent/script-action.now.ts` |
| `ApplicationMenu` | `@servicenow/sdk/core` | `sdk-reference/applicationmenu-sample/src/fluent/application-menu.now.ts` |
| `UIAction` | `@servicenow/sdk/core` | `sdk-reference/uiaction-sample/` |
| `UIPage` | `@servicenow/sdk/core` | `sdk-reference/uipage-sample/` |
| `List` | `@servicenow/sdk/core` | `sdk-reference/list-sample/src/fluent/list.now.ts` |
| `ATF` | `@servicenow/sdk/core` | `sdk-reference/test-atf-sample/` |

## Core Patterns

### Record (generic record on any table)
```typescript
import { Record } from '@servicenow/sdk/core'
Record({
    $id: Now.ID['<key-or-sys-id>'],
    table: '<table_name>',
    data: { /* field: value pairs */ },
})
```

### SPWidget
```typescript
import { SPWidget } from '@servicenow/sdk/core'
SPWidget({
    $id: Now.ID['<key>'],
    name: 'Widget Name',
    id: 'widget-id',
    clientScript: Now.include('file.client.js'),  // or inline string
    serverScript: Now.include('file.server.js'),
    htmlTemplate: Now.include('file.html'),
    customCss: Now.include('file.scss'),
    linkScript: `function link(scope, element, attrs, controller) {}`,
    optionSchema: [{ name, section, label, type, default_value, hint, choices }],
    angularProviders: ['<sys_id>'],
    dependencies: ['<sys_id>'],
    templates: [{ $id, id, htmlTemplate }],
    hasPreview: true,
    demoData: { data: {} },
})
```

### BusinessRule
```typescript
import { BusinessRule } from '@servicenow/sdk/core'
BusinessRule({
    $id: Now.ID['<key>'],
    name: 'Rule Name',
    active: true,
    table: '<table_name>',
    when: 'before',  // before | after | async | display
    script: Now.include('./script.server.js'),
})
```

### ACL
```typescript
import { Acl, Role } from '@servicenow/sdk/core'
export const admin = Role({ name: 'x_scope.admin' })
Acl({
    $id: Now.ID['<key>'],
    type: 'record',           // record | rest_endpoint
    operation: 'read',         // read | write | create | delete | execute
    table: '<table_name>',
    roles: [admin, 'x_scope.role'],
    condition: 'field=value',
    securityAttribute: 'user_is_authenticated',
})
```

## Utilities

| Function | Purpose | Example |
|---|---|---|
| `Now.include('./file.js')` | Include external script/template file | Keeps .now.ts clean |
| `Now.attach('./file.png')` | Attach binary asset (images, logos) | Portal logos, icons |
| `Now.ID['key']` | Type-safe record ID reference | Defined in `keys.ts` |

## keys.ts Structure

Declares record IDs for type-safe `Now.ID['key']` references:
- `explicit` keys: direct `{ table, id }` mappings
- `composite` keys: multi-field keys for m2m/junction tables

## File Conventions

| Extension | Purpose |
|---|---|
| `*.now.ts` | Fluent record definitions |
| `*.server.js` | Server-side scripts (GlideRecord, GlideSystem) |
| `*.client.js` | Client-side scripts (AngularJS, DOM) |

## Best Practices

See `servicenow-best-practices.md` for server-side and client-side scripting conventions (GlideRecord patterns, business rule guidelines, client script performance, debugging).

## When to Read Examples

- **Unsure about API parameters**: Read the relevant sample file from the table above
- **Creating a new artifact type**: Check if a sample exists in `sdk-reference/`
- **External file pattern**: See service-portal-sample for split client/server/html/scss
- **Dependencies/types**: See `sdk-reference/dependencies-sample/` for schema generation
