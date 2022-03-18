(
    'SELECT "ipif_hub_person"."id",
         "ipif_hub_person"."ipif_repo_id",
         "ipif_hub_person"."createdBy",
         "ipif_hub_person"."createdWhen",
         "ipif_hub_person"."modifiedBy",
         "ipif_hub_person"."modifiedWhen",
         "ipif_hub_person"."hubIngestedWhen",
         "ipif_hub_person"."hubModifiedWhen",
         "ipif_hub_person"."label" FROM "ipif_hub_person" INNER JOIN "ipif_hub_factoid" ON ("ipif_hub_person"."id" = "ipif_hub_factoid"."person_id") INNER JOIN "ipif_hub_factoid_statement" ON ("ipif_hub_factoid"."id" = "ipif_hub_factoid_statement"."factoid_id") WHERE ("ipif_hub_factoid_statement"."statement_id" IN (SELECT U0."id" FROM "ipif_hub_statement" U0 INNER JOIN "ipif_hub_statement_places" U1 ON (U0."id" = U1."statement_id") INNER JOIN "ipif_hub_place" U2 ON (U1."place_id" = U2."uri") WHERE U2."label" = %s) AND "ipif_hub_factoid_statement"."statement_id" IN (SELECT U0."id" FROM "ipif_hub_statement" U0 WHERE U0."role_label" = %s))', ('Graz', 'teacher'))



         ('SELECT "ipif_hub_person"."id", "ipif_hub_person"."ipif_repo_id", "ipif_hub_person"."createdBy", "ipif_hub_person"."createdWhen", "ipif_hub_person"."modifiedBy", "ipif_hub_person"."modifiedWhen", "ipif_hub_person"."hubIngestedWhen", "ipif_hub_person"."hubModifiedWhen", "ipif_hub_person"."label" FROM "ipif_hub_person" INNER JOIN "ipif_hub_factoid" ON ("ipif_hub_person"."id" = "ipif_hub_factoid"."person_id") INNER JOIN "ipif_hub_factoid_statement" ON ("ipif_hub_factoid"."id" = "ipif_hub_factoid_statement"."factoid_id") INNER JOIN "ipif_hub_factoid" T5 ON ("ipif_hub_person"."id" = T5."person_id") INNER JOIN "ipif_hub_factoid_statement" T6 ON (T5."id" = T6."factoid_id") INNER JOIN "ipif_hub_factoid" T8 ON ("ipif_hub_person"."id" = T8."person_id") INNER JOIN "ipif_hub_factoid_statement" T9 ON (T8."id" = T9."factoid_id") WHERE ("ipif_hub_factoid_statement"."statement_id" IN (SELECT U0."id" FROM "ipif_hub_statement" U0 INNER JOIN "ipif_hub_statement_places" U1 ON (U0."id" = U1."statement_id") INNER JOIN "ipif_hub_place" U2 ON (U1."place_id" = U2."uri") WHERE U2."label" = %s) AND T6."statement_id" IN (SELECT U0."id" FROM "ipif_hub_statement" U0 WHERE U0."role_label" = %s) AND T9."statement_id" IN (SELECT U0."id" FROM "ipif_hub_statement" U0 WHERE U0."role_label" = %s))',
 ('Graz', 'teacher', 'no'))