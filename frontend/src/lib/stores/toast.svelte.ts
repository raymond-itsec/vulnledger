type ToastVariant = 'error' | 'info' | 'success';

interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
}

let nextId = 1;
let items = $state<ToastItem[]>([]);
const timers = new Map<number, ReturnType<typeof setTimeout>>();

function remove(id: number) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  items = items.filter((item) => item.id !== id);
}

function push(message: string, variant: ToastVariant, duration = 3200) {
  const id = nextId++;
  items = [...items, { id, message, variant }];
  const timer = setTimeout(() => remove(id), duration);
  timers.set(id, timer);
  return id;
}

export const toast = {
  get items() {
    return items;
  },
  success(message: string, duration?: number) {
    return push(message, 'success', duration);
  },
  error(message: string, duration?: number) {
    return push(message, 'error', duration);
  },
  info(message: string, duration?: number) {
    return push(message, 'info', duration);
  },
  dismiss(id: number) {
    remove(id);
  },
};
