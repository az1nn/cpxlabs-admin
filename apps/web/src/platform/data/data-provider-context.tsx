import type { DataProvider } from '@cpxlabs-admin/contracts'
import { createContext, useContext, type PropsWithChildren } from 'react'

const DataProviderContext = createContext<DataProvider | null>(null)

type DataProviderProviderProps = PropsWithChildren<{
  provider: DataProvider
}>

export function DataProviderProvider({
  provider,
  children,
}: DataProviderProviderProps) {
  return (
    <DataProviderContext.Provider value={provider}>
      {children}
    </DataProviderContext.Provider>
  )
}

export function useDataProvider(): DataProvider {
  const provider = useContext(DataProviderContext)

  if (!provider) {
    throw new Error('useDataProvider must be used inside DataProviderProvider')
  }

  return provider
}
