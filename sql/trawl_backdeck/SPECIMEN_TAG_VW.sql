CREATE VIEW SPECIMEN_TAG_VW as
select
					sq2.*
					,case
						when row_number() over (partition by sq2.specimen_type, sq2.short_tag_id order by sq2.specimen_id) > 1 AND sq2.short_tag_id is not null
						then 1
						else 0
					end as DUPE_SHORT_TAG_FLAG
FROM			(
					select
										sq1.*
										,case
													when lower(sq1.specimen_type) in ('stomach id', 'tissue id') then sq1.vessel_id || sq1.specimen_number || coalesce(sq1.print_alpha_char, 'A')
													when lower(sq1.specimen_type) in ('ovary id', 'testis id') then sq1.vessel_id || sq1.haul_id || sq1.specimen_number || coalesce(sq1.print_alpha_char, 'A')
													else null
										end as SHORT_TAG_ID
					from (
								SELECT
													s.SPECIMEN_ID
													,s.alpha_value as TAG_ID
													,case when row_number() over (partition by s.alpha_value order by s.specimen_id) > 1 then 1 else 0 end as DUPE_TAG_FLAG
													,substr(s.alpha_value, 1, 4) as SURVEY_YR
													,substr(s.alpha_value, 6, 3) as VESSEL_ID
													,substr(s.alpha_value, 10, 3) as HAUL_ID
													,substr(s.alpha_value, 14, 3) as PI_ACTION_CODE_ID
													,substr(s.alpha_value, 18, 3) as SPECIMEN_NUMBER
													,case when length(s.alpha_value) > 20 then substr(s.alpha_value, (length(s.alpha_value) - 20) * -1) else null end as PRINT_ALPHA_CHAR
													,ta.type as SPECIMEN_TYPE
													,ta.subtype as SPECIMEN_SUBTYPE
								-- 					,s.cpu
													,s.NOTE
								FROM 			main."SPECIMEN" s
								left JOIN	main.TYPES_LU ta
													on s.action_type_id = ta.type_id

								WHERE			s.alpha_value like '%-%'
													and length(s.alpha_value) > 19
								) sq1
				) sq2