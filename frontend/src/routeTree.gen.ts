/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as VoterRecordsImport } from './routes/voter-records'
import { Route as PetitionImport } from './routes/petition'
import { Route as BallotsImport } from './routes/ballots'
import { Route as IndexImport } from './routes/index'

// Create/Update Routes

const VoterRecordsRoute = VoterRecordsImport.update({
  id: '/voter-records',
  path: '/voter-records',
  getParentRoute: () => rootRoute,
} as any)

const PetitionRoute = PetitionImport.update({
  id: '/petition',
  path: '/petition',
  getParentRoute: () => rootRoute,
} as any)

const BallotsRoute = BallotsImport.update({
  id: '/ballots',
  path: '/ballots',
  getParentRoute: () => rootRoute,
} as any)

const IndexRoute = IndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => rootRoute,
} as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexImport
      parentRoute: typeof rootRoute
    }
    '/ballots': {
      id: '/ballots'
      path: '/ballots'
      fullPath: '/ballots'
      preLoaderRoute: typeof BallotsImport
      parentRoute: typeof rootRoute
    }
    '/petition': {
      id: '/petition'
      path: '/petition'
      fullPath: '/petition'
      preLoaderRoute: typeof PetitionImport
      parentRoute: typeof rootRoute
    }
    '/voter-records': {
      id: '/voter-records'
      path: '/voter-records'
      fullPath: '/voter-records'
      preLoaderRoute: typeof VoterRecordsImport
      parentRoute: typeof rootRoute
    }
  }
}

// Create and export the route tree

export interface FileRoutesByFullPath {
  '/': typeof IndexRoute
  '/ballots': typeof BallotsRoute
  '/petition': typeof PetitionRoute
  '/voter-records': typeof VoterRecordsRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexRoute
  '/ballots': typeof BallotsRoute
  '/petition': typeof PetitionRoute
  '/voter-records': typeof VoterRecordsRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexRoute
  '/ballots': typeof BallotsRoute
  '/petition': typeof PetitionRoute
  '/voter-records': typeof VoterRecordsRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths: '/' | '/ballots' | '/petition' | '/voter-records'
  fileRoutesByTo: FileRoutesByTo
  to: '/' | '/ballots' | '/petition' | '/voter-records'
  id: '__root__' | '/' | '/ballots' | '/petition' | '/voter-records'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexRoute: typeof IndexRoute
  BallotsRoute: typeof BallotsRoute
  PetitionRoute: typeof PetitionRoute
  VoterRecordsRoute: typeof VoterRecordsRoute
}

const rootRouteChildren: RootRouteChildren = {
  IndexRoute: IndexRoute,
  BallotsRoute: BallotsRoute,
  PetitionRoute: PetitionRoute,
  VoterRecordsRoute: VoterRecordsRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/ballots",
        "/petition",
        "/voter-records"
      ]
    },
    "/": {
      "filePath": "index.tsx"
    },
    "/ballots": {
      "filePath": "ballots.tsx"
    },
    "/petition": {
      "filePath": "petition.tsx"
    },
    "/voter-records": {
      "filePath": "voter-records.tsx"
    }
  }
}
ROUTE_MANIFEST_END */
