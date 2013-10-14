.. _assistants in our Github repo: https://github.com/bkabrda/devassistant/tree/master/devassistant/assistants/assistants

.. _yaml_assistant_reference:

Yaml Assistant Reference
========================

*When developing assistants, please make sure that you read proper version
of documentation. The Yaml DSL of devassistant is still evolving rapidly,
so consider yourself warned.*

This is a reference manual to writing yaml assistants. Yaml assistants
use a special DSL defined on this page. For real examples, have a look
at `assistants in our Github repo`_.

*Why the hell another DSL?*
  When we started creating DevAssistant and we were asking people who
  work in various languages whether they'd consider contributing assistants
  for those languages, we hit the "I'm not touching Python" barrier. Since
  we wanted to keep the assistants consistent (centralized logging, sharing
  common functionality, same backtraces, etc...), we created a new DSL.
  So now we have something that everyone complains about, including Pythonists,
  which seems to be consistent too ;)

Assistant Roles
---------------
There are three types of assistants:

Creator
  creator assistants are meant to create new projects from scratch, they're
  accessed using ``da`` binary
Modifier
  modifier assistants are used for modifying existing projects previously
  created by DevAssistant
Preparer
  preparer assistants are used for setting up environment for already existing
  projects (located e.g. at remote SCM etc.) that may or may not have been
  creating by DevAssistant

The role is implied by assistant location in one of the load path directories,
as mentioned in :ref:`assistants_loading_mechanism`.

All the rules mentioned in this document apply to all types of assistants,
with exception of sections :ref:`modifier_assistants_ref` and
:ref:`preparer_assistants_ref` that talk about specifics of Modifier, resp.
Preparer assistants.

Assistant Name
--------------

Assistant name is a short name used on command line, e.g. ``python``. It
should also be the only top-level yaml mapping in the file (that means
just one assistant per file). Each assistant should be placed in a file
that's named the same as the assistant itself (e.g. ``python`` assistant
in ``python.yaml`` file).

Assistant Content
-----------------

The top level mapping has to be mapping from assistant name to assistant
attributes, for example::

   python:
     fullname: Python
     # etc.

List of allowed attributes follows (all of them are optional, and have some
sort of reasonable default, it's up to your consideration which of them to use):

``fullname``
  a verbose name that will be displayed to user (``Python Assistant``)
``description``
  a (verbose) description to show to user (``Bla bla create project bla bla``)
``dependencies`` (and ``dependencies_*``)
  specification of dependencies, see below `Dependencies`_
``args``
  specification of arguments, see below `Args`_
``files``
  specification of used files, see below `Files`_
``run`` (and ``run_*``)
  specification of actual operations, see below `Run`_
``files_dir``
  directory where to take files (templates, helper scripts, ...) from. Defaults
  to base directory from where this assistant is taken + ``files``. E.g. if
  this assistant is ``~/.devassistant/assistants/crt/path/and/more.yaml``,
  files will be taken from ``~/.devassistant/files/crt/path/and/more`` by default.
``icon_path``
  absolute or relative path to icon of this assistant (will be used by GUI).
  If not present, a default path will be used - this is derived from absolute
  assistant path by replacing ``assistants`` by ``icons`` and ``.yaml`` by
  ``.svg`` - e.g. for ``~/.devassistant/assistants/crt/foo/bar.yaml``,
  the default icon path is ``~/.devassistant/icons/crt/foo/bar.svg``

Dependencies
------------

Yaml assistants can express their dependencies in multiple sections.

- Packages from section ``dependencies`` are **always** installed.
- If there is a section named ``dependencies_foo``, then dependencies from this section are installed
  **iff** ``foo`` argument is used (either via commandline or via gui). For example::

   $ da python --foo

- These rules differ for `Modifier Assistants`_

Each section contains a list of mappings ``dependency type: [list, of, deps]``.
If you provide more mappings like this::

   dependencies:
   - rpm: [foo]
   - rpm: ["@bar"]

they will be traversed and installed one by one. Supported dependency types: 

``rpm``
  the dependency list can contain RPM packages or YUM groups
  (groups must begin with ``@`` and be quoted, e.g. ``"@Group name"``)
``call``
  installs dependencies from snippet or other dependency section of this assistant. For example::

   dependencies:
   - call: foo # will install dependencies from snippet "foo", section "dependencies"
   - call: foo.dependencies_bar # will install dependencies from snippet "foo", section "bar"
   - call: self.dependencies_baz # will install dependencies from section "dependencies_baz" of this assistant

``if``, ``else``
  conditional dependency installation. For more info on conditions, `Run`_ below.
  A very simple example::

   dependencies:
   - if $foo:
     - rpm: [bar]
   - else:
     - rpm: [spam]

Full example::

   dependencies: - rpm: [foo, "@bar"]

   dependencies_spam:
   - rpm: [beans, eggs]
   - if $with_spam:
     - call: spam.spamspam
   - rpm: [ham]

Args
----

Arguments are used for specifying commandline arguments or gui inputs.
Every assistant can have zero to multiple arguments.

The ``args`` section of each yaml assistant is a mapping of arguments to
their attributes::

   args:
     name:
       flags:
       - -n
       - --name
     help: Name of the project to create.
 
Available argument attributes:

``flags``
  specifies commandline flags to use for this argument. The longer flag
  (without the ``--``, e.g. ``name`` from ``--name``) will hold the specified
  commandline/gui value during ``run`` section, e.g. will be accessible as ``$name``.
``help``
  a help string
``required``
  one of ``{true,false}`` - is this argument required?
``nargs``
  how many parameters this argument accepts, one of ``{?,*,+}``
  (e.g. {0 or 1, 0 or more, 1 or more})
``default``
  a default value (this will cause the default value to be
  set even if the parameter wasn't used by user)
``action``
  one of ``{store_true, [default_iff_used, value]}`` - the ``store_true`` value
  will create a switch from the argument, so it won't accept any
  parameters; the ``[default_iff_used, value]`` will cause the argument to
  be set to default value ``value`` **iff** it was used without parameters
  (if it wasn't used, it won't be defined at all)
``snippet``
  name of the snippet to load this argument from; any other specified attributes
  will override those from the snippet By convention, some arguments
  should be common to all or most of the assistants.
  See :ref:`common_assistant_behaviour`

Gui Hints
~~~~~~~~~

GUI needs to work with arguments dynamically, choose proper widgets and offer
sensible default values to user. These are not always automatically
retrieveable from arguments that suffice for commandline. For example, GUI
cannot meaningfully prefill argument that says it "defaults to current working
directory". Also, it cannot tell whether to choose a widget for path (with the
"Browse ..." button) or just a plain text field.

Because of that, each argument can have ``gui_hints`` attribute.
This can specify that this argument is of certain type (path/str/bool) and
has a certain default. If not specified in ``gui_hints``, the default is
taken from the argument itself, if not even there, a sensible "empty" default
value is used (home directory/empty string/false). For example::

   args:
     path:
       flags:
       - [-p, --path]
       gui_hints:
         type: path
         default: $(pwd)/foo

If you want your assistant to work properly with GUI, it is good to use
``gui_hints`` (currently, it only makes sense to use it for ``path``
attributes, as ``str`` and ``bool`` get proper widgets and default values
automatically).

Files
-----

This section serves as a list of aliases of files stored in one of the
``files`` dirs of DevAssistant. E.g. if your assistant is
``assistants/crt/foo/bar.yaml``, then files are taken relative to
``files/crt/foo/bar/`` directory. So if you have a file
``files/crt/foo/bar/spam``, you can use::

   files:
     spam: &spam
       source: spam

This will allow you to reference the ``spam`` file in ``run`` section as
``*spam`` without having to know where exactly it is located in your
installation of DevAssistant.

Run
---

Run sections are the essence of DevAssistant. They are responsible for
preforming all the tasks and actions to set up the environment and
the project itself. By default, section named ``run`` is invoked
(this is a bit different for `Modifier Assistants`_).
If there is a section named ``run_foo`` and ``foo`` argument is used,
then **only** ``run_foo`` is invoked. This is different from
dependencies sections, as the default ``dependencies`` section is used
every time.

Every ``run`` section is a sequence of various commands, mostly
invocations of commandline. Each command is a mapping
``command_type: command``. During the execution, you may use logging
(messages will be printed to terminal or gui) with following levels:
``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``. By default,
messages of level ``INFO`` and higher are logged. As you can see below,
there is a separate ``log_*`` command type for logging, but some other
command types can also log various messages. Log messages with levels
``ERROR`` and ``CRITICAL`` terminate execution of DevAssistant imediatelly.

Run sections allow you to use variables with certain rules and
limitations. See below.

List of supported commands follows:

``cl``
  runs given command on commandline, aborts execution of the invoked assistant if it fails.
  **Note:** ``cd`` is a special cased command, which doesn't do shell expansion other than
  user home dir (``~``) expansion.
``cl_i``
  the ``i`` option makes the command execution be logged at ``INFO`` level
  (default is ``DEBUG``), therefore visible to user
``log_[diwec]``
  logs given message at level specified by the last letter in ``log_X``.
  If the level is ``e`` or ``c``, the execution of the assistant is interrupted immediately.
``dda_{c,dependencies,run}``
  - ``c`` creates ``.devassistant`` file (containing some sane initial meta
    information about the project) in given directory
  - ``dda_dependencies`` let's you install dependencies from ``.devassistant`` file
    (DevAssistant will use dependencies from original assistant and specified 
    ``dependencies`` attribute, if any - this has the same structure as ``dependencies``
    in normal assistants, and is evaluated in current assistant context, not the original
    assistant context)
  - ``dda_run`` will execute a series of commands from ``run`` section from
    ``.devassistant`` (in context of current assistant)
``if <expression>``, ``else``
  conditional execution. The condition must be an `Expression`_.
``for <var> in <expression>``
  (for example ``for $i in $(ls)``) - loop over *result* of given expression
  (if it is string, which almost always is, it is split on whitespaces)
``$foo``
  assigns *result* of an `Expression`_ to the given variable
  (doesn't interrupt the assistant execution if command fails)
``$success, $foo``
  assigns *logical result* (``True``/``False``) of evaluating an `Expression`_ to
  ``$success`` and result to ``$foo`` (same as above)
``call``
  run another section of this assistant (e.g.``call: self.run_foo``) of a snippet
  run section (``call: snippet_name.run_foo``) at this place and then continue execution
``scl``
  run a whole section in SCL environment of one or more SCLs (note: you **must**
  use the scriptlet name - usually ``enable`` - because it might vary) - for example::

   run:
   - scl enable python33 postgresql92:
     - cl_i: python --version
     - cl_i: pgsql --version

Variables
~~~~~~~~~

Initially, variables are populated with values of arguments from
commandline/gui and there are no other variables defined for creator
assistants. For modifier assistants global variables are prepopulated
with some values read from ``.devassistant``. You can either define
(and assign to) your own variables or change the values of current ones.

The variable scope works as follows:

- When invoking ``run`` section (from the current assistant or snippet),
  the variables get passed by value (e.g. they don't get modified for the
  remainder of this scope).
- As you would probably expect, variables that get modified in ``if`` and
  ``else`` sections are modified until the end of the current scope.

All variables are global in the sense that if you call a snippet or another
section, it can see all the arguments that are defined.

.. _Expression:

Expressions
~~~~~~~~~~~

Expressions are expressions, really. They are used in assignments, conditions
and as loop "iterables". Every expression has a *logical result* (meaning
success - ``True`` or failure - ``False``) and *result* (meaning output).
*Logical result* is used in conditions and variable assignments, *result*
is used in variable assignments and loops.
Note: when assigned to a variable, the *logical result* of an expression can
be used in conditions as expected; the *result* is either ``True``/``False``.

Syntax and semantics:

- ``$foo``

  - if ``$foo`` is defined:

    - *logical result*: ``True`` **iff** value is not empty and it is not
      ``False``
    - *result*: value of ``$foo``
  - otherwise:

    - *logical result*: ``False``
    - *result*: empty string
- ``$(commandline command)`` (yes, that is a command invocation that looks like
  running command in a subshell)

  - if ``commandline command`` has return value 0:

    - *logical result*: ``True``

  - otherwise:

    - *logical result*: ``False``

  - regardless of *logical result*, *result* always contains both stdout
    and stderr lines in the order they were printed by ``commandline command``

- ``defined $foo`` works exactly as ``$foo``, but has *logical result*
  ``True`` even if the value is empty or ``False``

- ``not $foo`` negates the *logical result* of an expression, while leaving
  *result* intact

- ``$foo and $bar``

  - *logical result* is logical conjunction of the two arguments

  - *result* is either empty string if one of the arguments is empty string or the latter argument

- ``$foo or $bar``

  - *logical result* is logical disjunction of the two arguments

  - *result* is the first non-empty argument or an empty string

- ``literals - "foo"``

  - *logical result* ``True`` for non-empty strings, ``False`` otherwise
    
  - *result* is the string itself, sans quotes

- ``$foo in $bar``

  - *logical result* is ``True`` if the second argument contains the first, e. g. "inus" in "Linus Torvalds", and ``False`` otherwise

  - *result* is always the first argument

All these can of course be chained together, so for instance ``"1.8.1.4" in $(git --version) and defined $git`` is also a valid expression.


Quoting
~~~~~~~

When using variables that contain user input, they should always be
quoted in the places where they are used for bash execution. That
includes ``cl*`` commands, conditions that use bash return values and
variable assignment that uses bash.

.. _modifier_assistants_ref:

Modifier Assistants
-------------------

Modifier assistants are assistants that are supposed to work with
already created project. They must be placed under ``mod``
subdirectory of one of the load paths, as mentioned in
:ref:`assistants_loading_mechanism`.

There are few special things about modifier assistants:

- They read the whole .devassistant file and make its contents available
  as any other variables (notably ``$subassistant_path``).
- They use dependency sections according to the normal rules + they use *all*
  the sections that are named according to loaded ``$subassistant_path``,
  e.g. if ``$subassistant_path`` is ``[foo, bar]``, dependency sections
  ``dependencies``, ``dependencies_foo`` and ``dependencies_foo_bar`` will
  be used as well as any sections that would get installed according to
  specified parameters. The rationale behind this is, that if you have e.g.
  ``eclipse`` modifier that should work for both ``python django`` and
  ``python flask`` projects, chance is that they have some common dependencies,
  e.g. ``eclipse-pydev``. So you can just place these common dependencies in
  ``dependencies_python`` and you're done (you can possibly place special
  per-framework dependencies into e.g. ``dependencies_python_django``).
- By default, they don't use ``run`` section. Assuming that ``$subassistant_path``
  is ``[foo, bar]``, they first try to find ``run_foo_bar``, then ``run_foo``
  and then just ``run``. The first found is used. If you however use cli/gui
  parameter ``spam`` and section ``run_spam`` is present, then this is run instead.

.. _preparer_assistants_ref:

Preparer Assistants
-------------------

Preparer assistants are assistants that are supposed to set up environment for
executing arbitrary tasks or prepare environment and checkout existing upstream
projects (possibly using their ``.devassistant`` file, if they have it).
Preparers must be placed under ``prep`` subdirectory of one of the load
paths, as mentioned in :ref:`assistants_loading_mechanism`.

Preparer assistants commonly utilize the ``dda_dependencies`` and ``dda_run``
commands in ``run`` section.
