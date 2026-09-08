import type { ApplicationRole } from '@cpxlabs-admin/contracts'

import type { PrismaClient } from '../../generated/prisma/client.js'

export type AccessProfileStatus = 'active' | 'disabled'

export type AccessProfile = {
  id: string
  userId: string
  role: ApplicationRole
  status: AccessProfileStatus
}

export type AccessProfileRepository = {
  getByUserId(userId: string): Promise<AccessProfile | null>
  upsert(input: {
    userId: string
    role: ApplicationRole
    status?: AccessProfileStatus
  }): Promise<AccessProfile>
  setStatus(userId: string, status: AccessProfileStatus): Promise<AccessProfile>
}

function toAccessProfile(record: {
  id: string
  userId: string
  role: ApplicationRole
  status: AccessProfileStatus
}): AccessProfile {
  return record
}

export class PrismaAccessProfileRepository implements AccessProfileRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async getByUserId(userId: string): Promise<AccessProfile | null> {
    const profile = await this.prisma.accessProfile.findUnique({ where: { userId } })
    return profile ? toAccessProfile(profile) : null
  }

  async upsert(input: {
    userId: string
    role: ApplicationRole
    status?: AccessProfileStatus
  }): Promise<AccessProfile> {
    const status = input.status ?? 'active'
    const profile = await this.prisma.accessProfile.upsert({
      where: { userId: input.userId },
      update: { role: input.role, status },
      create: {
        userId: input.userId,
        role: input.role,
        status,
      },
    })
    return toAccessProfile(profile)
  }

  async setStatus(userId: string, status: AccessProfileStatus): Promise<AccessProfile> {
    const profile = await this.prisma.accessProfile.update({
      where: { userId },
      data: { status },
    })
    return toAccessProfile(profile)
  }
}
