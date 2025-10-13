---
title: "{{TITLE}}"
abbrev: "{{ABBREV}}"
category: {{CATEGORY}}

docname: {{DOCNAME}}-latest
submissiontype: IETF
number:
date: {{DATE}}
consensus: true
v: 3
area: "{{AREA}}"
workgroup: "{{WORKGROUP}}"
keyword:
{{#each KEYWORDS}}
 - {{this}}
{{/each}}
venue:
  group: "{{WORKGROUP}}"
  type: "Working Group"
  mail: "{{MAIL}}"
  arch: "{{ARCHIVE}}"
  github: "{{GITHUB}}"
  latest: "{{LATEST_URL}}"

author:
{{#each AUTHORS}}
 -
  fullname: {{fullname}}
  organization: {{organization}}
  email: {{email}}
{{/each}}

normative:

informative:

--- abstract

{{ABSTRACT}}

--- middle

# Introduction

{{INTRODUCTION}}

# Conventions and Definitions

{::boilerplate bcp14-tagged}

# Terminology

{{TERMINOLOGY_SECTION}}

# Interfaces

{{INTERFACES_SECTION}}

# Behavior

{{BEHAVIOR_SECTION}}

# Security Considerations

{{SECURITY_SECTION}}

# IANA Considerations

{{IANA_SECTION}}

--- back

# Acknowledgments
{:numbered="false"}

{{ACKNOWLEDGMENTS}}
