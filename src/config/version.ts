import { Platform } from 'react-native';
import * as Application from 'expo-application';
import { version } from '../../package.json';

export interface VersionInfo {
  version: string;
  buildNumber: string;
  bundleId: string;
}

export const getVersionInfo = async (): Promise<VersionInfo> => {
  if (Platform.OS === 'ios') {
    return {
      version: Application.nativeApplicationVersion ?? version,
      buildNumber: Application.nativeBuildVersion ?? '1',
      bundleId: Application.applicationId ?? 'com.securepass.generator',
    };
  }

  if (Platform.OS === 'android') {
    return {
      version: Application.nativeApplicationVersion ?? version,
      buildNumber: Application.nativeBuildVersion ?? '1',
      bundleId: Application.applicationId ?? 'com.securepass.generator',
    };
  }

  // Web or other platforms
  return {
    version,
    buildNumber: '1',
    bundleId: 'com.securepass.generator',
  };
};

export const formatVersion = (info: VersionInfo): string => {
  return `${info.version} (${info.buildNumber})`;
};

export const compareVersions = (a: string, b: string): number => {
  const aParts = a.split('.').map(Number);
  const bParts = b.split('.').map(Number);

  for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
    const aPart = aParts[i] || 0;
    const bPart = bParts[i] || 0;
    if (aPart !== bPart) {
      return aPart - bPart;
    }
  }
  return 0;
};
