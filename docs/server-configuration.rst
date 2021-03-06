
====================
Server Configuration
====================

You can pass a configuration file to the Scrapy Do daemon in the following way:

  .. code-block:: console

       $ scrapy-do scrapy-do --config /path/to/config/file.conf

The remaining part of this section describes the meaning of the configurable
parameters.

-----------------------
``[scrapy-do]`` section
-----------------------

* **project-store**: A directory where all the state of the Scrapy Do daemon is
  stored. Defaults to ``projects``, meaning that it will use a subdirectory of
  the Current Working Directory.

* **job-slots**: A numer of jobs that can run in parallel. Defaults to ``3``.

* **completed-cap**: A number of completed jobs to keep. All the jobs that exceed
  the cap and their log files will be purged. Older jobs are purged first.
  Defaults to ``50``.

-----------------
``[web]`` section
-----------------

* **interfaces**: A whitespace-separated list of address-port pairs to listen
  on. Use the RFC3986 notation to specify IPv6 addresses, i.e., ``[::1]:7654``.
  Defaults to ``127.0.0.1:7654``.

* **https**: The HTTPS switch. Defaults to ``off``.

* **key**: Path to your certificate key. Defaults to: ``scrapy-do.key``.

* **cert**: Path to your certificate. Defaults to: ``scrapy-do.crt``.

* **chain**: Path to a file containing additional certificates in the chain of
  trust. Useful when using Let's Encrypt because their signing certificate
  is trusted by browsers but not by OS iteslf, leading to commadnline tools like
  `wget` or `curl` failing to verify the certificate. Defaults to an empty
  string.

* **auth**: The authentication switch. Scrapy Do uses the digest authentication
  method and it will not transmit your password over the network. Therefore,
  it's safe to use even without TLS. Defaults to ``off``.

* **auth-db**: Path to your authentication database file. The file contains
  username-password pairs, each in a separate line. The user and password parts
  are separated by a colon (``:``). I.e., ``myusername:mypassword``. Please note
  that the digest authentication requires the server to know the actual password
  and not the hash. Defaults to ``auth.db``.

---------------------
Example configuration
---------------------

  .. code-block:: ini

       [scrapy-do]
       project-store = /var/scrapy-do
       job-slots = 5
       completed-cap = 250

       [web]
       interfaces = 10.8.0.1:9999 [2001:db8::fa]:7654

       https = on
       key = /etc/scrapy-do/scrapy-do.key
       cert = /etc/scrapy-do/scrapy-do.crt
       chain = /etc/scrapy-do/scrapy-do-chain.pem

       auth = on
       auth-db = /etc/scrapy-do/auth.db
