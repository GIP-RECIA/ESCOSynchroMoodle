FROM osixia/openldap:1.2.2
LABEL maintainer="Rémi Alvergnat <remi.alvergnat@gfi.fr>"

RUN rm -Rf /container/service/slapd/assets/config/bootstrap/schema/mmc
 
COPY ldap/schema/*.schema /container/service/slapd/assets/config/bootstrap/schema/
COPY ldap/ldif/*.ldif /container/service/slapd/assets/config/bootstrap/ldif/custom/
