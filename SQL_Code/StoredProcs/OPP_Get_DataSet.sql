if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_DataSet]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_DataSet]
go

-- Copyright � OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_DataSet

@pr_session_id    int,
@pr_language      varchar(20),
@pr_dataset_name  varchar(64),
@pr_time_period   varchar(64),
@p_result_status  varchar (255) output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  set @pr_dataset_name = isnull(@pr_dataset_name, 'NOTSET')

  if (@pr_dataset_name = 'OPG001')
    select * from dbo.OPG001

  else if (@pr_dataset_name = 'OPG010')
    select * from dbo.OPG010

  else if (@pr_dataset_name = 'OPG001C')
    select * from dbo.OPG001C

  else if (@pr_dataset_name = 'OPG011')
    if (@pr_time_period = 'last-month')
        select null [OPG Data Set],
               null [Hierarchy One Name],
               dur.[Hierarchy1] as [H0],
               case
                when dur.[Hierarchy1] = dur.[Hierarchy2] then '' else dur.[Hierarchy2]
               end as [H1],
               case
                when dur.[Hierarchy2] = dur.[Hierarchy3] then '' else dur.[Hierarchy3]
               end as [H2],
               case
                when dur.[Hierarchy3] = dur.[Hierarchy4] then '' else dur.[Hierarchy4]
               end as [H3],
               case
                when dur.[Hierarchy4] = dur.[Hierarchy5] then '' else dur.[Hierarchy5]
               end as [H4],
               dur.[HierarchyLeaf] as [H5],
               -- dur.[HierarchyLeaf] as [Hierarchy Value],
               -- 5 as [Hierarchy Level],
               dur.[DocumentType] as [Variable Name],
               dur.[DocumentTypeQualifier] as [Variable Name Qualifier],
               dur.[DocumentTypeSubQualifier] as [Variable Name Sub Qualifier],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then dur.[DocumentTypeSubQualifier]
    --              else dur.[DocumentTypeQualifier]
    --            end as [Variable Value],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then 2
    --              else 1
    --            end as [Variable Level],
               dur.[EventDate] as [Date of Event],
               --null [Year of Event],
               --null [Quarter],
               --null [Month of Event],
               --null [Week of Event],
               --null [Fiscal Year of Event],
               --null [Fiscal Quarter],
               --null [Fiscal Month of Event],
               --null [Fiscal Week of Event],
               --null [Julian Day],
               dur.[ActivityId] as [Activity Event Id],
               dur.[Measure1],
               dur.[Measure2],
               dur.[Measure3],
               dur.[PartialPeriod] as [Partial Period]
          from dbo.OPG011_eventData as dur with (nolock) where [EventDate] >= DATEADD( month, -1, GETDATE())

    else if (@pr_time_period = 'last-quarter')
        select null [OPG Data Set],
               null [Hierarchy One Name],
               dur.[Hierarchy1] as [H0],
               case
                when dur.[Hierarchy1] = dur.[Hierarchy2] then '' else dur.[Hierarchy2]
               end as [H1],
               case
                when dur.[Hierarchy2] = dur.[Hierarchy3] then '' else dur.[Hierarchy3]
               end as [H2],
               case
                when dur.[Hierarchy3] = dur.[Hierarchy4] then '' else dur.[Hierarchy4]
               end as [H3],
               case
                when dur.[Hierarchy4] = dur.[Hierarchy5] then '' else dur.[Hierarchy5]
               end as [H4],
               dur.[HierarchyLeaf] as [H5],
               -- dur.[HierarchyLeaf] as [Hierarchy Value],
               -- 5 as [Hierarchy Level],
               dur.[DocumentType] as [Variable Name],
               dur.[DocumentTypeQualifier] as [Variable Name Qualifier],
               dur.[DocumentTypeSubQualifier] as [Variable Name Sub Qualifier],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then dur.[DocumentTypeSubQualifier]
    --              else dur.[DocumentTypeQualifier]
    --            end as [Variable Value],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then 2
    --              else 1
    --            end as [Variable Level],
               dur.[EventDate] as [Date of Event],
               --null [Year of Event],
               --null [Quarter],
               --null [Month of Event],
               --null [Week of Event],
               --null [Fiscal Year of Event],
               --null [Fiscal Quarter],
               --null [Fiscal Month of Event],
               --null [Fiscal Week of Event],
               --null [Julian Day],
               dur.[ActivityId] as [Activity Event Id],
               dur.[Measure1],
               dur.[Measure2],
               dur.[Measure3],
               dur.[PartialPeriod] as [Partial Period]
          from dbo.OPG011_eventData as dur with (nolock) where [EventDate] >= DATEADD( quarter, -1, GETDATE())

    else if (@pr_time_period = 'last-year')
        select null [OPG Data Set],
               null [Hierarchy One Name],
               dur.[Hierarchy1] as [H0],
               case
                when dur.[Hierarchy1] = dur.[Hierarchy2] then '' else dur.[Hierarchy2]
               end as [H1],
               case
                when dur.[Hierarchy2] = dur.[Hierarchy3] then '' else dur.[Hierarchy3]
               end as [H2],
               case
                when dur.[Hierarchy3] = dur.[Hierarchy4] then '' else dur.[Hierarchy4]
               end as [H3],
               case
                when dur.[Hierarchy4] = dur.[Hierarchy5] then '' else dur.[Hierarchy5]
               end as [H4],
               dur.[HierarchyLeaf] as [H5],
               -- dur.[HierarchyLeaf] as [Hierarchy Value],
               -- 5 as [Hierarchy Level],
               dur.[DocumentType] as [Variable Name],
               dur.[DocumentTypeQualifier] as [Variable Name Qualifier],
               dur.[DocumentTypeSubQualifier] as [Variable Name Sub Qualifier],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then dur.[DocumentTypeSubQualifier]
    --              else dur.[DocumentTypeQualifier]
    --            end as [Variable Value],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then 2
    --              else 1
    --            end as [Variable Level],
               dur.[EventDate] as [Date of Event],
               --null [Year of Event],
               --null [Quarter],
               --null [Month of Event],
               --null [Week of Event],
               --null [Fiscal Year of Event],
               --null [Fiscal Quarter],
               --null [Fiscal Month of Event],
               --null [Fiscal Week of Event],
               --null [Julian Day],
               dur.[ActivityId] as [Activity Event Id],
               dur.[Measure1],
               dur.[Measure2],
               dur.[Measure3],
               dur.[PartialPeriod] as [Partial Period]
          from dbo.OPG011_eventData as dur with (nolock) where [EventDate] >= DATEADD( year, -1, GETDATE())
--     select --null [OPG Data Set],
--            --null [Hierarchy One Name],
--            --null [Hierarchy One Top],
--            --null [Hierarchy One -1],
--            --null [Hierarchy One -2],
--            --null [Hierarchy One -3],
--            --null [Hierarchy One -4],
--            dur.[Hierarchy One Leaf] as [Hierarchy Value],
--            5 as [Hierarchy Level],
--            --[Variable Name],
--            --[Variable Name Qualifier],
--            --[Variable Name Sub Qualifier],
--            case
--              when isnull(dur.[Variable Name Sub Qualifier], '') <> '' then dur.[Variable Name Sub Qualifier]
--              else dur.[Variable Name Qualifier]
--            end as [Variable Value],
--            case
--              when isnull(dur.[Variable Name Sub Qualifier], '') <> '' then 2
--              else 1
--            end as [Variable Level],
--            dur.[Date of Event],
--            dur.[Calendar Entry Type],
--            --null [Year of Event],
--            --null [Quarter],
--            --null [Month of Event],
--            --null [Week of Event],
--            --null [Fiscal Year of Event],
--            --null [Fiscal Quarter],
--            --null [Fiscal Month of Event],
--            --null [Fiscal Week of Event],
--            --null [Julian Day],
--            dur.[Activity Event Id],
--            dur.[Measure Value],
--            dur.[Measure Type],
--            -- TODO: COMMENTED OUT TO BE ADDED AS A FEATURE LATER
--            --           --[Measure Value],
--            --           --[Measure Type],
--            --           dur.[Measure Value] as [Measure Value 1],
--            --           dur.[Measure Type] as [Measure Type 1],
--            --           cou.[Measure Value] as [Measure Value 2],
--            --           cou.[Measure Type] as [Measure Type 2],
--            --           dol.[Measure Value] as [Measure Value 3],
--            --           dol.[Measure Type] as [Measure Type 3],
--            --           null as [Measure Value 4],
--            --           null as [Measure Type 4],
--            --           null as [Measure Value 5],
--            --           null as [Measure Type 5],
--            dur.[Partial Period]
--       from dbo.OPG001 as dur with (nolock)
--       left outer join dbo.OPG001 as cou with (nolock)
--         on cou.[Measure Type] = 'Count'
--        and cou.[Date of Event] = dur.[Date of Event]
--        and cou.[Calendar Entry Type] = 'Week'
--        and trim(isnull(cou.[Variable Name Qualifier], '')) = trim(isnull(dur.[Variable Name Qualifier], ''))
--        and trim(isnull(cou.[Hierarchy One Leaf], '')) = trim(isnull(dur.[Hierarchy One Leaf], ''))
--        and trim(isnull(cou.[Hierarchy One -1], '')) = trim(isnull(dur.[Hierarchy One -1], ''))
--        and trim(isnull(cou.[Hierarchy One -2], '')) = trim(isnull(dur.[Hierarchy One -2], ''))
--        and trim(isnull(cou.[Hierarchy One -3], '')) = trim(isnull(dur.[Hierarchy One -3], ''))
--        and trim(isnull(cou.[Hierarchy One -4], '')) = trim(isnull(dur.[Hierarchy One -4], ''))
--       left outer join dbo.OPG001 as dol with (nolock)
--         on dol.[Measure Type] = 'Dollar'
--        and dol.[Date of Event] = dur.[Date of Event]
--        and dol.[Calendar Entry Type] = 'Week'
--        and trim(isnull(dol.[Variable Name Qualifier], '')) = trim(isnull(dur.[Variable Name Qualifier], ''))
--        and trim(isnull(dol.[Hierarchy One Leaf], '')) = trim(isnull(dur.[Hierarchy One Leaf], ''))
--        and trim(isnull(dol.[Hierarchy One -1], '')) = trim(isnull(dur.[Hierarchy One -1], ''))
--        and trim(isnull(dol.[Hierarchy One -2], '')) = trim(isnull(dur.[Hierarchy One -2], ''))
--        and trim(isnull(dol.[Hierarchy One -3], '')) = trim(isnull(dur.[Hierarchy One -3], ''))
--        and trim(isnull(dol.[Hierarchy One -4], '')) = trim(isnull(dur.[Hierarchy One -4], ''))
--      where trim(isnull(dur.[Hierarchy One Leaf], '')) <> ''
--        -- we can't prune based on Sub Qualifier because the data is 'blown out',
--        -- but since the data doesn't include any values in Sub Qualifier, we are ok
--        and trim(isnull(dur.[Variable Name Qualifier], '')) <> ''
--        and dur.[Calendar Entry Type] = 'Week'
    else
        select null [OPG Data Set],
               null [Hierarchy One Name],
               dur.[Hierarchy1] as [H0],
               case
                when dur.[Hierarchy1] = dur.[Hierarchy2] then '' else dur.[Hierarchy2]
               end as [H1],
               case
                when dur.[Hierarchy2] = dur.[Hierarchy3] then '' else dur.[Hierarchy3]
               end as [H2],
               case
                when dur.[Hierarchy3] = dur.[Hierarchy4] then '' else dur.[Hierarchy4]
               end as [H3],
               case
                when dur.[Hierarchy4] = dur.[Hierarchy5] then '' else dur.[Hierarchy5]
               end as [H4],
               dur.[HierarchyLeaf] as [H5],
               -- dur.[HierarchyLeaf] as [Hierarchy Value],
               -- 5 as [Hierarchy Level],
               dur.[DocumentType] as [Variable Name],
               dur.[DocumentTypeQualifier] as [Variable Name Qualifier],
               dur.[DocumentTypeSubQualifier] as [Variable Name Sub Qualifier],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then dur.[DocumentTypeSubQualifier]
    --              else dur.[DocumentTypeQualifier]
    --            end as [Variable Value],
    --            case
    --              when isnull(dur.[DocumentTypeSubQualifier], '') <> '' then 2
    --              else 1
    --            end as [Variable Level],
               dur.[EventDate] as [Date of Event],
               --null [Year of Event],
               --null [Quarter],
               --null [Month of Event],
               --null [Week of Event],
               --null [Fiscal Year of Event],
               --null [Fiscal Quarter],
               --null [Fiscal Month of Event],
               --null [Fiscal Week of Event],
               --null [Julian Day],
               dur.[ActivityId] as [Activity Event Id],
               dur.[Measure1],
               dur.[Measure2],
               dur.[Measure3],
               dur.[PartialPeriod] as [Partial Period]
          from dbo.OPG011_eventData as dur with (nolock)
  else
  begin
    set @p_result_status = 'OPP_Get_Dataset001|Invalid dataset name: ' + @pr_dataset_name
    return
  end

  set @p_result_status = 'OK'
end


-- EOF