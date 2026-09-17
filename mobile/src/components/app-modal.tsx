import type { PropsWithChildren } from 'react';
import { Modal, Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Colors, Spacing } from '@/constants/theme';

interface AppModalProps extends PropsWithChildren {
  visible: boolean;
  title: string;
  onClose: () => void;
}

export function AppModal({ visible, title, onClose, children }: AppModalProps) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable onPress={(e) => e.stopPropagation()} style={styles.sheetWrapper}>
          <ThemedView card style={styles.sheet}>
            <View style={styles.header}>
              <ThemedText type="subtitle">{title}</ThemedText>
              <Pressable onPress={onClose} hitSlop={12}>
                <ThemedText color="muted" style={styles.close}>
                  ✕
                </ThemedText>
              </Pressable>
            </View>
            {children}
          </ThemedView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  sheetWrapper: {
    maxHeight: '85%',
  },
  sheet: {
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
    padding: Spacing.four,
    gap: Spacing.three,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  close: {
    fontSize: 18,
    color: Colors.muted,
  },
});
