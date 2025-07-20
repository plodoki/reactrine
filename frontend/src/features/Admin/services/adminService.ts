import { AdminService } from '../../../lib/api-client';
import type {
  UserList,
  RoleList,
  UserRoleUpdate,
  UserWithRole,
} from '../../../lib/api-client';
import type { UserDeletionResponse } from '../../../types/api';
import '../../../lib/api-client-config'; // Ensure the client is configured

interface GetUsersParams {
  limit?: number;
  offset?: number;
  email?: string;
}

export const adminService = {
  async getUsers(params: GetUsersParams = {}): Promise<UserList> {
    return await AdminService.listUsersApiV1AdminUsersGet({
      limit: params.limit,
      offset: params.offset,
      email: params.email,
    });
  },

  async getUser(userId: number): Promise<UserWithRole> {
    return await AdminService.getUserApiV1AdminUsersUserIdGet({
      userId,
    });
  },

  async getRoles(): Promise<RoleList> {
    return await AdminService.listRolesApiV1AdminRolesGet();
  },

  async updateUserRole(
    userId: number,
    roleUpdate: UserRoleUpdate
  ): Promise<UserWithRole> {
    return await AdminService.updateUserRoleApiV1AdminUsersUserIdRolePut({
      userId,
      requestBody: roleUpdate,
    });
  },

  /**
   * Update user status (enable/disable)
   */
  async updateUserStatus(userId: number, isActive: boolean): Promise<UserWithRole> {
    return await AdminService.updateUserStatusApiV1AdminUsersUserIdStatusPatch({
      userId,
      requestBody: { is_active: isActive },
    });
  },

  /**
   * Permanently delete a user
   */
  async deleteUser(userId: number): Promise<UserDeletionResponse> {
    return await AdminService.deleteUserAccountApiV1AdminUsersUserIdDelete({
      userId,
    });
  },
};
