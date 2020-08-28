CREATE VIEW SPECIMEN_TAG_VW as
with spec as (
	SELECT
                s.SPECIMEN_ID
                ,s.alpha_value as TAG_ID
                ,substr(s.alpha_value, 1, 4) as SURVEY_YR
                ,substr(s.alpha_value, 6, 3) as VESSEL_ID
                ,substr(s.alpha_value, 10, 3) as HAUL_ID
                ,substr(s.alpha_value, 14, 3) as PI_ACTION_CODE_ID
                ,substr(s.alpha_value, 18, 3) as SPECIMEN_NUMBER
                ,case when length(s.alpha_value) > 20 then substr(s.alpha_value, (length(s.alpha_value) - 20) * -1) else null end as PRINT_ALPHA_CHAR
                ,ta.type as SPECIMEN_TYPE
                ,ta.subtype as SPECIMEN_SUBTYPE
                ,s.CPU
                ,s.NOTE
                ,case
                    when lower(ta.type) in ('stomach id', 'tissue id')
                    then substr(s.alpha_value, 6, 3)
                                || substr(s.alpha_value, 18, 3)
                                || coalesce(case when length(s.alpha_value) > 20 then substr(s.alpha_value, (length(s.alpha_value) - 20) * -1) else null end, 'A')
                    when lower(ta.type) in ('ovary id', 'testis id')
                    then substr(s.alpha_value, 6, 3)
                                || substr(s.alpha_value, 10, 3)
                                || substr(s.alpha_value, 18, 3)
                                || coalesce(case when length(s.alpha_value) > 20 then substr(s.alpha_value, (length(s.alpha_value) - 20) * -1) else null end, 'A')
                    else null
                end as SHORT_TAG_ID
    FROM 		main."SPECIMEN" s
    left JOIN	main.TYPES_LU ta
                on s.action_type_id = ta.type_id
    WHERE		s.alpha_value like '%-%'
                and length(s.alpha_value) > 19
)

select		distinct
            t1.specimen_id
            ,t1.survey_yr
            ,t1.vessel_id
            ,t1.haul_id
            ,t1.PI_ACTION_CODE_ID
            ,t1.specimen_number
            ,t1.print_alpha_char
            ,t1.specimen_type
            ,t1.specimen_subtype
            ,t1.note
            ,t1.tag_id
            ,case when t2.tag_id is null then 0 else 1 end as DUPLICATE_TAG
            ,t1.short_tag_id
            ,case when t3.short_tag_id is null then 0 else 1 end as DUPLICATE_SHORT_TAG
            ,t1.cpu
FROM		spec t1
left JOIN	(
            select
                    row_number() over (partition by tag_id order by specimen_id) as rn
                    ,tag_id
            from 	spec
            ) t2
            on t1.tag_id = t2.tag_id
            and t2.rn > 1
left JOIN   (
            select
                    row_number() over (partition by specimen_type, short_tag_id order by specimen_id) as rn
                    ,short_tag_id
                    ,specimen_type
            FROM    spec
            ) t3
            on t1.short_tag_id = t3.short_tag_id
            and t1.specimen_type = t3.specimen_type
            and t3.rn > 1