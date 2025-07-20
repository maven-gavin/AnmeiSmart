import { UserRole } from "./auth";

export interface MenuItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  roles: UserRole[];
  children?: MenuItem[];
}

export interface MenuConfig {
  items: MenuItem[];
} 