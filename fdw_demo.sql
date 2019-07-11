-- I hand-rolled the DDL for this with a bunch of it being code-generated from introspecting the FooBar Library.
-- The parameter_domain values were obtained from a cross product of the domains of each variable (i.e. modelling_domain and kind) and then attempting to construct
-- a library and filtering out any pair that caused an exception

/*
class FdwLibrary(ForeignDataWrapper):
    def __init__(self, options, columns):
        super(FdwLibrary, self).__init__(options, columns)
        self.columns = columns
        self.options = options.copy()
        self.library = self.options['library']

*/

CREATE foreign table "foobar.LoadingsLib" -- we use the symbol of the callable to create the library as the name of the table.
( id integer, -- from the axes
  date date,  -- from the axes
  modelling_domain varchar,  -- parameter
  kind varchar,  -- parameter
  -- all these come from Library.nodes
  "AltCyclic" double precision NULL, -- PostgreSQL will lowercase the column names unless they are quoted
  "Alt_Cyclicals" double precision NULL, -- The double-quote is the standard quoting syntax for SQL .. the [] is SQL-Server specific
  "Aviation_etc" double precision
  -- etc. etc.
) server library_srv options(
    library 'foobar.LoadingsLib', -- this is the name of the callable to construct the library
    parameters '["modelling_domain","kind"]', -- the parameters as a JSON-encoded list
    axes '[{"dtype": "date:date[Basic/day]", "name": "date"},{"dtype": "id:integer", "name": "id"}]', -- axes as JSON-encoded metadata
    -- A list of all legitimate parameter tuples
    parameter_domain '[["D","COMPUTED"], ["D, "HISTORICAL"], ["G", "COMPUTED"],
     ["G","HISTORICAL"], ["GO", "HISTORICAL"], ["JC", "COMPUTED"],
     ["J","HISTORICAL"], ["JO", "HISTORICAL"], ["US", "COMPUTED"],
     ["U", "HISTORICAL"], ["UO", "HISTORICAL"]]'
);





-- This is the per-user blob of JSON that FooBar uses to construct an ipyparallel.Client to talk
-- to a backend that does the expression evaluation

ALTER user mapping for CURRENT_USER SERVER library_srv OPTIONS( ipyparallel '

{ "control": 59192,
  "task": 55274,
  "notification": 40003,
  "task_scheme": "leastload",
  "mux": 53178,
  "iopub": 55995,
  "ssh": "",
  "key": "<redacted>",
  "registration": 40586,
  "interface": "tcp://127.0.0.1",
  "signature_scheme": "hmac-sha256",
  "pack": "json",
  "unpack": "json",
  "location": "<redacted>"
}')

;
